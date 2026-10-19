from datetime import date
from flask import Blueprint,flash,g,redirect,render_template,request,url_for,abort
from ..decorators import permission_required,role_required
from ..extensions import db
from ..forms import AssessmentForm,AttendanceForm,GradeForm
from ..models import AcademicCalendar,AcademicClass,Assessment,Attendance,Enrollment,Grade
from ..services.audit import audit
from ..services.academic import calculate_summary
teacher_bp=Blueprint('teacher',__name__,url_prefix='/professor')
def _teacher():
    if not g.current_user.teacher: abort(403)
    return g.current_user.teacher
def _class(cid):
    c=db.get_or_404(AcademicClass,cid)
    if c.teacher_id!=_teacher().id: abort(403)
    return c
@teacher_bp.get('/')
@role_required('teacher')
def dashboard():
    cs=db.session.execute(db.select(AcademicClass).where(AcademicClass.teacher_id==_teacher().id,AcademicClass.is_active.is_(True)).order_by(AcademicClass.code)).scalars().all()
    ids={c.semester_id for c in cs}; events=db.session.execute(db.select(AcademicCalendar).where(AcademicCalendar.semester_id.in_(ids or [-1]),AcademicCalendar.event_date>=date.today()).order_by(AcademicCalendar.event_date).limit(6)).scalars().all()
    return render_template('dashboards/teacher.html',classes=cs,upcoming=events)
@teacher_bp.get('/turmas')
@permission_required('teacher.classes.view')
def classes(): return render_template('teacher/classes.html',rows=db.session.execute(db.select(AcademicClass).where(AcademicClass.teacher_id==_teacher().id).order_by(AcademicClass.code)).scalars().all())
@teacher_bp.get('/turmas/<int:cid>')
@permission_required('teacher.classes.view')
def class_detail(cid): return render_template('teacher/class_detail.html',academic_class=_class(cid))
@teacher_bp.route('/turmas/<int:cid>/avaliacoes/nova',methods=['GET','POST'])
@permission_required('teacher.grades.write')
def assessment_new(cid):
    c=_class(cid); form=AssessmentForm()
    if form.validate_on_submit():
        a=Assessment(class_id=c.id,title=form.title.data.strip(),assessment_date=form.assessment_date.data,max_score=form.max_score.data,weight=form.weight.data); db.session.add(a); db.session.commit(); audit(g.current_user.id,'assessment_created','assessment',a.id,{'class_id':c.id}); flash('Avaliação criada.','success'); return redirect(url_for('teacher.grades',cid=cid))
    return render_template('teacher/assessment_form.html',form=form,academic_class=c)
@teacher_bp.get('/turmas/<int:cid>/notas')
@permission_required('teacher.grades.write')
def grades(cid):
    c=_class(cid); assessments=db.session.execute(db.select(Assessment).where(Assessment.class_id==cid).order_by(Assessment.assessment_date)).scalars().all(); aid=request.args.get('assessment',type=int) or (assessments[0].id if assessments else None); selected=db.session.get(Assessment,aid) if aid else None
    if selected and selected.class_id!=cid: abort(403)
    return render_template('teacher/grades.html',academic_class=c,assessments=assessments,selected=selected,GradeForm=GradeForm)
@teacher_bp.post('/turmas/<int:cid>/notas/<int:aid>/<int:eid>')
@permission_required('teacher.grades.write')
def grade_save(cid,aid,eid):
    c=_class(cid); a=db.get_or_404(Assessment,aid); e=db.get_or_404(Enrollment,eid)
    if a.class_id!=c.id or e.class_id!=c.id: abort(403)
    form=GradeForm()
    if form.validate_on_submit():
        if form.score.data>a.max_score: flash(f'A nota não pode ultrapassar {a.max_score}.','danger'); return redirect(url_for('teacher.grades',cid=cid,assessment=aid))
        gobj=db.session.execute(db.select(Grade).where(Grade.assessment_id==aid,Grade.enrollment_id==eid)).scalar_one_or_none(); action='grade_updated' if gobj else 'grade_created'
        if gobj: gobj.score=form.score.data; gobj.entered_by=g.current_user.id
        else: gobj=Grade(assessment_id=aid,enrollment_id=eid,score=form.score.data,entered_by=g.current_user.id); db.session.add(gobj)
        db.session.commit(); audit(g.current_user.id,action,'grade',gobj.id,{'assessment_id':aid,'enrollment_id':eid}); flash('Nota salva.','success')
    else: flash('Nota inválida.','danger')
    return redirect(url_for('teacher.grades',cid=cid,assessment=aid))
@teacher_bp.route('/turmas/<int:cid>/frequencia',methods=['GET','POST'])
@permission_required('teacher.attendance.write')
def attendance(cid):
    c=_class(cid); es=db.session.execute(db.select(Enrollment).where(Enrollment.class_id==cid,Enrollment.status=='active').order_by(Enrollment.student_id)).scalars().all(); form=AttendanceForm()
    sel=request.args.get('date')
    try:
        selected=date.fromisoformat(sel) if sel else date.today()
    except ValueError:
        abort(400)
    if form.validate_on_submit():
        d=form.attendance_date.data
        for e in es:
            st=request.form.get(f'status_{e.id}')
            if st not in {'present','absent','justified'}: flash('Status de frequência inválido.','danger'); return render_template('teacher/attendance.html',academic_class=c,enrollments=es,form=form,selected_date=d)
            rec=db.session.execute(db.select(Attendance).where(Attendance.enrollment_id==e.id,Attendance.attendance_date==d)).scalar_one_or_none()
            if rec: rec.status=st; rec.recorded_by=g.current_user.id
            else: db.session.add(Attendance(enrollment_id=e.id,attendance_date=d,status=st,recorded_by=g.current_user.id))
        db.session.commit(); audit(g.current_user.id,'attendance_saved','class',cid,{'date':str(d)}); flash('Frequência salva.','success'); return redirect(url_for('teacher.attendance',cid=cid,date=d.isoformat()))
    form.attendance_date.data=selected; return render_template('teacher/attendance.html',academic_class=c,enrollments=es,form=form,selected_date=selected)
@teacher_bp.get('/calendario')
@permission_required('teacher.calendar.view')
def calendar():
    ids=db.select(AcademicClass.semester_id).where(AcademicClass.teacher_id==_teacher().id).distinct(); rows=db.session.execute(db.select(AcademicCalendar).where(AcademicCalendar.semester_id.in_(ids)).order_by(AcademicCalendar.event_date)).scalars().all(); return render_template('teacher/calendar.html',rows=rows)

@teacher_bp.get('/alunos/<int:student_id>/historico')
@permission_required('teacher.history.view')
def student_history(student_id):
    student_enrollments=db.session.execute(db.select(Enrollment).join(Enrollment.academic_class).where(Enrollment.student_id==student_id, AcademicClass.teacher_id==_teacher().id).order_by(Enrollment.id.desc())).scalars().all()
    if not student_enrollments: abort(404)
    return render_template('teacher/student_history.html', student=student_enrollments[0].student, summaries=[(e, calculate_summary(e)) for e in student_enrollments])
