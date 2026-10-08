from datetime import date
from flask import Blueprint,g,render_template
from ..decorators import permission_required,role_required
from ..extensions import db
from ..models import AcademicCalendar,Enrollment
from ..services.academic import calculate_summary
student_bp=Blueprint('student',__name__,url_prefix='/aluno')
def _student():
    from flask import abort
    if not g.current_user.student: abort(403)
    return g.current_user.student
def _enrollments(): return db.session.execute(db.select(Enrollment).where(Enrollment.student_id==_student().id,Enrollment.status=='active').order_by(Enrollment.id.desc())).scalars().all()
@student_bp.get('/')
@role_required('student')
def dashboard():
    es=_enrollments(); ids={e.academic_class.semester_id for e in es}; events=db.session.execute(db.select(AcademicCalendar).where(AcademicCalendar.semester_id.in_(ids or [-1]),AcademicCalendar.event_date>=date.today()).order_by(AcademicCalendar.event_date).limit(6)).scalars().all()
    return render_template('dashboards/student.html',student=_student(),summaries=[(e,calculate_summary(e)) for e in es],upcoming=events)
@student_bp.get('/academico')
@permission_required('student.academic.view')
def academic():
    es=_enrollments(); return render_template('student/academic.html',summaries=[(e,calculate_summary(e)) for e in es])
@student_bp.get('/historico')
@role_required('student')
def history():
    es=db.session.execute(db.select(Enrollment).where(Enrollment.student_id==_student().id).order_by(Enrollment.id.desc())).scalars().all()
    return render_template('student/history.html', student=_student(), summaries=[(e,calculate_summary(e)) for e in es])
@student_bp.get('/horario')
@role_required('student')
def schedule(): return render_template('student/schedule.html',classes=[e.academic_class for e in _enrollments()])
@student_bp.get('/calendario')
@permission_required('student.calendar.view')
def calendar():
    ids={e.academic_class.semester_id for e in _enrollments()}; rows=db.session.execute(db.select(AcademicCalendar).where(AcademicCalendar.semester_id.in_(ids or [-1])).order_by(AcademicCalendar.event_date)).scalars().all(); return render_template('student/calendar.html',rows=rows)
@student_bp.get('/perfil')
@role_required('student')
def profile(): return render_template('student/profile.html',student=_student())
