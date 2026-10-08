from __future__ import annotations

from datetime import date
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import func, or_, select

from teofac.decorators import permission_required
from teofac.extensions import db
from teofac.forms import (
    AcademicClassForm,
    AcademicEventForm,
    CourseForm,
    EnrollmentForm,
    PermissionForm,
    SemesterForm,
    StudentForm,
    SubjectForm,
    TeacherForm,
    UserAdminForm,
)
from teofac.models import (
    AcademicCalendar,
    AcademicClass,
    Administrator,
    AuditLog,
    Course,
    Enrollment,
    Permission,
    Semester,
    Student,
    Subject,
    Teacher,
    User,
    UserPermission,
)
from teofac.services.academic import calculate_summary
from teofac.services.audit import log_event
from teofac.services.permissions import grant_role_permissions

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _set_choices(form):
    form.course_id.choices = [(c.id, f"{c.code} — {c.name}") for c in Course.query.filter_by(is_active=True).order_by(Course.name).all()]


def _set_subject_choices(form):
    form.course_id.choices = [(c.id, f"{c.code} — {c.name}") for c in Course.query.filter_by(is_active=True).order_by(Course.name).all()]


def _set_class_choices(form):
    form.subject_id.choices = [
        (s.id, f"{s.code} — {s.name}")
        for s in Subject.query.filter_by(is_active=True).order_by(Subject.name).all()
    ]
    form.semester_id.choices = [
        (s.id, f"{s.code} — {s.name}")
        for s in Semester.query.order_by(Semester.start_date.desc()).all()
    ]
    form.teacher_id.choices = [(0, "Sem professor vinculado")] + [
        (t.id, f"{t.user.full_name} ({t.employee_number})")
        for t in Teacher.query.join(Teacher.user).filter(User.is_active.is_(True)).order_by(User.full_name).all()
    ]


def _set_calendar_choices(form):
    form.semester_id.choices = [
        (s.id, f"{s.code} — {s.name}")
        for s in Semester.query.order_by(Semester.start_date.desc()).all()
    ]


@bp.get("/")
@permission_required("admin.dashboard")
def dashboard():
    current_semester = Semester.query.filter_by(is_current=True).first()
    counts = {
        "students": Student.query.join(Student.user).filter(User.is_active.is_(True)).count(),
        "teachers": Teacher.query.join(Teacher.user).filter(User.is_active.is_(True)).count(),
        "courses": Course.query.filter_by(is_active=True).count(),
        "subjects": Subject.query.filter_by(is_active=True).count(),
        "classes": AcademicClass.query.filter_by(is_active=True).count(),
    }
    upcoming = AcademicCalendar.query.filter(AcademicCalendar.event_date >= date.today())
    if current_semester:
        upcoming = upcoming.filter(AcademicCalendar.semester_id == current_semester.id)
    upcoming = upcoming.order_by(AcademicCalendar.event_date.asc()).limit(5).all()
    return render_template("admin/dashboard.html", counts=counts, current_semester=current_semester, upcoming=upcoming)


@bp.get("/alunos")
@permission_required("students.manage")
def students():
    q = request.args.get("q", "").strip()
    query = Student.query.join(Student.user)
    if q:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                Student.registration_number.ilike(f"%{q}%"),
            )
        )
    page = max(request.args.get("page", 1, type=int), 1)
    pagination = query.order_by(User.full_name).paginate(page=page, per_page=25, error_out=False)
    return render_template("admin/students.html", students=pagination.items, pagination=pagination, q=q)


@bp.route("/alunos/novo", methods=["GET", "POST"])
@permission_required("students.manage")
def student_new():
    form = StudentForm()
    _set_choices(form)
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Usuário ou e-mail já cadastrado.", "error")
        else:
            user = User(
                username=username,
                email=form.email.data.lower().strip(),
                full_name=form.full_name.data.strip(),
                role="student",
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            student = Student(
                user_id=user.id,
                registration_number=form.registration_number.data.strip(),
                course_id=form.course_id.data,
                birth_date=form.birth_date.data,
                phone=form.phone.data.strip() if form.phone.data else None,
                address=form.address.data.strip() if form.address.data else None,
            )
            db.session.add(student)
            db.session.commit()
            grant_role_permissions(user)
            log_event("user.created", "student", user.id, {"username": user.username})
            flash("Aluno cadastrado com sucesso.", "success")
            return redirect(url_for("admin.students"))
    return render_template("admin/student_form.html", form=form, title="Novo aluno")


@bp.route("/alunos/<int:student_id>/editar", methods=["GET", "POST"])
@permission_required("students.manage")
def student_edit(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        abort(404)
    form = StudentForm(obj=student)
    form.username.data = student.user.username
    form.email.data = student.user.email
    form.full_name.data = student.user.full_name
    _set_choices(form)
    if form.validate_on_submit():
        duplicate = User.query.filter(
            User.id != student.user_id,
            or_(User.username == form.username.data.strip().lower(), User.email == form.email.data.lower().strip())
        ).first()
        if duplicate:
            flash("Usuário ou e-mail já utilizado por outro usuário.", "error")
        else:
            student.user.username = form.username.data.strip().lower()
            student.user.email = form.email.data.lower().strip()
            student.user.full_name = form.full_name.data.strip()
            if form.password.data:
                student.user.set_password(form.password.data)
            student.registration_number = form.registration_number.data.strip()
            student.course_id = form.course_id.data
            student.birth_date = form.birth_date.data
            student.phone = form.phone.data.strip() if form.phone.data else None
            student.address = form.address.data.strip() if form.address.data else None
            db.session.commit()
            log_event("user.updated", "student", student.user_id, {"student_id": student.id})
            flash("Aluno atualizado com sucesso.", "success")
            return redirect(url_for("admin.students"))
    return render_template("admin/student_form.html", form=form, title="Editar aluno", student=student)


@bp.post("/alunos/<int:student_id>/alternar-status")
@permission_required("students.manage")
def student_toggle(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        abort(404)
    student.user.is_active = not student.user.is_active
    db.session.commit()
    log_event("user.status_changed", "student", student.user_id, {"active": student.user.is_active})
    flash("Status do aluno atualizado.", "success")
    return redirect(url_for("admin.students"))


@bp.get("/professores")
@permission_required("teachers.manage")
def teachers():
    q = request.args.get("q", "").strip()
    query = Teacher.query.join(Teacher.user)
    if q:
        query = query.filter(or_(User.full_name.ilike(f"%{q}%"), Teacher.employee_number.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    page = max(request.args.get("page", 1, type=int), 1)
    pagination = query.order_by(User.full_name).paginate(page=page, per_page=25, error_out=False)
    return render_template("admin/teachers.html", teachers=pagination.items, pagination=pagination, q=q)


@bp.route("/professores/novo", methods=["GET", "POST"])
@permission_required("teachers.manage")
def teacher_new():
    form = TeacherForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Usuário ou e-mail já cadastrado.", "error")
        else:
            user = User(username=username, email=form.email.data.lower().strip(), full_name=form.full_name.data.strip(), role="teacher")
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            db.session.add(Teacher(user_id=user.id, employee_number=form.employee_number.data.strip(), specialization=form.specialization.data.strip() if form.specialization.data else None))
            db.session.commit()
            grant_role_permissions(user)
            log_event("user.created", "teacher", user.id, {"username": user.username})
            flash("Professor cadastrado com sucesso.", "success")
            return redirect(url_for("admin.teachers"))
    return render_template("admin/teacher_form.html", form=form, title="Novo professor")


@bp.route("/professores/<int:teacher_id>/editar", methods=["GET", "POST"])
@permission_required("teachers.manage")
def teacher_edit(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        abort(404)
    form = TeacherForm(obj=teacher)
    form.username.data = teacher.user.username
    form.email.data = teacher.user.email
    form.full_name.data = teacher.user.full_name
    if form.validate_on_submit():
        duplicate = User.query.filter(
            User.id != teacher.user_id,
            or_(User.username == form.username.data.strip().lower(), User.email == form.email.data.lower().strip())
        ).first()
        if duplicate:
            flash("Usuário ou e-mail já utilizado por outro usuário.", "error")
        else:
            teacher.user.username = form.username.data.strip().lower()
            teacher.user.email = form.email.data.lower().strip()
            teacher.user.full_name = form.full_name.data.strip()
            if form.password.data:
                teacher.user.set_password(form.password.data)
            teacher.employee_number = form.employee_number.data.strip()
            teacher.specialization = form.specialization.data.strip() if form.specialization.data else None
            db.session.commit()
            log_event("user.updated", "teacher", teacher.user_id, {"teacher_id": teacher.id})
            flash("Professor atualizado com sucesso.", "success")
            return redirect(url_for("admin.teachers"))
    return render_template("admin/teacher_form.html", form=form, title="Editar professor", teacher=teacher)


@bp.post("/professores/<int:teacher_id>/alternar-status")
@permission_required("teachers.manage")
def teacher_toggle(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        abort(404)
    teacher.user.is_active = not teacher.user.is_active
    db.session.commit()
    log_event("user.status_changed", "teacher", teacher.user_id, {"active": teacher.user.is_active})
    flash("Status do professor atualizado.", "success")
    return redirect(url_for("admin.teachers"))


@bp.get("/cursos")
@permission_required("courses.manage")
def courses():
    return render_template("admin/courses.html", courses=Course.query.order_by(Course.name).all())


@bp.route("/cursos/novo", methods=["GET", "POST"])
@permission_required("courses.manage")
def course_new():
    form = CourseForm()
    if form.validate_on_submit():
        db.session.add(Course(code=form.code.data.upper().strip(), name=form.name.data.strip(), description=form.description.data.strip() if form.description.data else None, duration_semesters=form.duration_semesters.data))
        db.session.commit()
        flash("Curso criado com sucesso.", "success")
        log_event("course.created", "course")
        return redirect(url_for("admin.courses"))
    return render_template("admin/course_form.html", form=form, title="Novo curso")


@bp.route("/cursos/<int:course_id>/editar", methods=["GET", "POST"])
@permission_required("courses.manage")
def course_edit(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.code = form.code.data.upper().strip()
        course.name = form.name.data.strip()
        course.description = form.description.data.strip() if form.description.data else None
        course.duration_semesters = form.duration_semesters.data
        course.is_active = form.is_active.data
        db.session.commit()
        flash("Curso atualizado.", "success")
        log_event("course.updated", "course", course.id)
        return redirect(url_for("admin.courses"))
    return render_template("admin/course_form.html", form=form, title="Editar curso", course=course)


@bp.get("/disciplinas")
@permission_required("subjects.manage")
def subjects():
    rows = Subject.query.join(Subject.course).order_by(Course.name, Subject.semester_number, Subject.name).all()
    return render_template("admin/subjects.html", subjects=rows)


@bp.route("/disciplinas/nova", methods=["GET", "POST"])
@permission_required("subjects.manage")
def subject_new():
    form = SubjectForm()
    _set_subject_choices(form)
    if form.validate_on_submit():
        db.session.add(Subject(course_id=form.course_id.data, code=form.code.data.upper().strip(), name=form.name.data.strip(), workload_hours=form.workload_hours.data, semester_number=form.semester_number.data))
        db.session.commit()
        flash("Disciplina criada.", "success")
        log_event("subject.created", "subject")
        return redirect(url_for("admin.subjects"))
    return render_template("admin/subject_form.html", form=form, title="Nova disciplina")


@bp.route("/disciplinas/<int:subject_id>/editar", methods=["GET", "POST"])
@permission_required("subjects.manage")
def subject_edit(subject_id):
    subject = db.session.get(Subject, subject_id)
    if not subject:
        abort(404)
    form = SubjectForm(obj=subject)
    _set_subject_choices(form)
    if form.validate_on_submit():
        subject.course_id = form.course_id.data
        subject.code = form.code.data.upper().strip()
        subject.name = form.name.data.strip()
        subject.workload_hours = form.workload_hours.data
        subject.semester_number = form.semester_number.data
        subject.is_active = form.is_active.data
        db.session.commit()
        flash("Disciplina atualizada.", "success")
        log_event("subject.updated", "subject", subject.id)
        return redirect(url_for("admin.subjects"))
    return render_template("admin/subject_form.html", form=form, title="Editar disciplina", subject=subject)


@bp.get("/periodos")
@permission_required("semesters.manage")
def semesters():
    return render_template("admin/semesters.html", semesters=Semester.query.order_by(Semester.start_date.desc()).all())


@bp.route("/periodos/novo", methods=["GET", "POST"])
@permission_required("semesters.manage")
def semester_new():
    form = SemesterForm()
    if form.validate_on_submit():
        if form.is_current.data:
            Semester.query.update({Semester.is_current: False}, synchronize_session=False)
        semester = Semester(code=form.code.data.upper().strip(), name=form.name.data.strip(), start_date=form.start_date.data, end_date=form.end_date.data, is_current=form.is_current.data, minimum_average=form.minimum_average.data, minimum_attendance_pct=form.minimum_attendance_pct.data, maximum_absences=form.maximum_absences.data, number_of_assessments=form.number_of_assessments.data, recovery_enabled=form.recovery_enabled.data)
        db.session.add(semester)
        db.session.commit()
        flash("Período letivo criado.", "success")
        log_event("semester.created", "semester", semester.id)
        return redirect(url_for("admin.semesters"))
    return render_template("admin/semester_form.html", form=form, title="Novo período letivo")


@bp.route("/periodos/<int:semester_id>/editar", methods=["GET", "POST"])
@permission_required("semesters.manage")
def semester_edit(semester_id):
    semester = db.session.get(Semester, semester_id)
    if not semester:
        abort(404)
    form = SemesterForm(obj=semester)
    if form.validate_on_submit():
        if form.is_current.data:
            Semester.query.filter(Semester.id != semester.id).update({Semester.is_current: False}, synchronize_session=False)
        semester.code = form.code.data.upper().strip()
        semester.name = form.name.data.strip()
        semester.start_date = form.start_date.data
        semester.end_date = form.end_date.data
        semester.is_current = form.is_current.data
        semester.minimum_average = form.minimum_average.data
        semester.minimum_attendance_pct = form.minimum_attendance_pct.data
        semester.maximum_absences = form.maximum_absences.data
        semester.number_of_assessments = form.number_of_assessments.data
        semester.recovery_enabled = form.recovery_enabled.data
        db.session.commit()
        flash("Período letivo atualizado.", "success")
        log_event("semester.updated", "semester", semester.id)
        return redirect(url_for("admin.semesters"))
    return render_template("admin/semester_form.html", form=form, title="Editar período letivo", semester=semester)


@bp.get("/turmas")
@permission_required("classes.manage")
def classes():
    rows = AcademicClass.query.join(AcademicClass.subject).join(AcademicClass.semester).order_by(AcademicClass.is_active.desc(), Semester.start_date.desc(), Subject.name, AcademicClass.code).all()
    return render_template("admin/classes.html", classes=rows)


@bp.route("/turmas/nova", methods=["GET", "POST"])
@permission_required("classes.manage")
def class_new():
    form = AcademicClassForm()
    _set_class_choices(form)
    if form.validate_on_submit():
        teacher_id = form.teacher_id.data or None
        item = AcademicClass(subject_id=form.subject_id.data, semester_id=form.semester_id.data, teacher_id=teacher_id, code=form.code.data.upper().strip(), room=form.room.data.strip() if form.room.data else None, weekday=form.weekday.data, start_time=form.start_time.data, end_time=form.end_time.data, is_active=form.is_active.data)
        db.session.add(item)
        db.session.commit()
        flash("Turma criada.", "success")
        log_event("class.created", "class", item.id)
        return redirect(url_for("admin.classes"))
    return render_template("admin/class_form.html", form=form, title="Nova turma")


@bp.route("/turmas/<int:class_id>/editar", methods=["GET", "POST"])
@permission_required("classes.manage")
def class_edit(class_id):
    item = db.session.get(AcademicClass, class_id)
    if not item:
        abort(404)
    form = AcademicClassForm(obj=item)
    form.teacher_id.data = item.teacher_id or 0
    _set_class_choices(form)
    if form.validate_on_submit():
        item.subject_id = form.subject_id.data
        item.semester_id = form.semester_id.data
        item.teacher_id = form.teacher_id.data or None
        item.code = form.code.data.upper().strip()
        item.room = form.room.data.strip() if form.room.data else None
        item.weekday = form.weekday.data
        item.start_time = form.start_time.data
        item.end_time = form.end_time.data
        item.is_active = form.is_active.data
        db.session.commit()
        flash("Turma atualizada.", "success")
        log_event("class.updated", "class", item.id)
        return redirect(url_for("admin.classes"))
    return render_template("admin/class_form.html", form=form, title="Editar turma", academic_class=item)


@bp.route("/turmas/<int:class_id>", methods=["GET", "POST"])
@permission_required("enrollments.manage")
def class_detail(class_id):
    item = db.session.get(AcademicClass, class_id)
    if not item:
        abort(404)
    form = EnrollmentForm()
    _existing = select(Enrollment.student_id).where(Enrollment.class_id == item.id)
    form.student_id.choices = [
        (s.id, f"{s.user.full_name} — {s.registration_number}")
        for s in Student.query.join(Student.user).filter(User.is_active.is_(True), ~Student.id.in_(_existing)).order_by(User.full_name).all()
    ]
    if form.validate_on_submit():
        student = db.session.get(Student, form.student_id.data)
        if not student or not student.user.is_active:
            flash("Aluno inválido.", "error")
        elif Enrollment.query.filter_by(student_id=student.id, class_id=item.id).first():
            flash("Aluno já está matriculado nesta turma.", "error")
        else:
            enrollment = Enrollment(student_id=student.id, class_id=item.id)
            db.session.add(enrollment)
            db.session.commit()
            log_event("enrollment.created", "enrollment", enrollment.id, {"class_id": item.id, "student_id": student.id})
            flash("Matrícula realizada.", "success")
        return redirect(url_for("admin.class_detail", class_id=item.id))
    item.enrollments.sort(key=lambda e: e.student.user.full_name.lower())
    return render_template("admin/class_detail.html", academic_class=item, form=form)


@bp.post("/matriculas/<int:enrollment_id>/remover")
@permission_required("enrollments.manage")
def enrollment_remove(enrollment_id):
    enrollment = db.session.get(Enrollment, enrollment_id)
    if not enrollment:
        abort(404)
    class_id = enrollment.class_id
    enrollment.status = "dropped"
    db.session.commit()
    log_event("enrollment.removed", "enrollment", enrollment.id, {"class_id": class_id})
    flash("Matrícula removida.", "success")
    return redirect(url_for("admin.class_detail", class_id=class_id))


@bp.get("/calendario")
@permission_required("calendar.manage")
def calendar():
    events = AcademicCalendar.query.join(AcademicCalendar.semester).order_by(AcademicCalendar.event_date.desc(), AcademicCalendar.title).all()
    return render_template("admin/calendar.html", events=events)


@bp.route("/calendario/novo", methods=["GET", "POST"])
@permission_required("calendar.manage")
def calendar_new():
    form = AcademicEventForm()
    _set_calendar_choices(form)
    if form.validate_on_submit():
        event = AcademicCalendar(semester_id=form.semester_id.data, title=form.title.data.strip(), description=form.description.data.strip() if form.description.data else None, event_date=form.event_date.data, event_type=form.event_type.data)
        db.session.add(event)
        db.session.commit()
        flash("Evento incluído no calendário.", "success")
        log_event("calendar.created", "academic_calendar", event.id)
        return redirect(url_for("admin.calendar"))
    return render_template("admin/calendar_form.html", form=form, title="Novo evento")


@bp.route("/calendario/<int:event_id>/editar", methods=["GET", "POST"])
@permission_required("calendar.manage")
def calendar_edit(event_id):
    event = db.session.get(AcademicCalendar, event_id)
    if not event:
        abort(404)
    form = AcademicEventForm(obj=event)
    _set_calendar_choices(form)
    if form.validate_on_submit():
        event.semester_id = form.semester_id.data
        event.title = form.title.data.strip()
        event.description = form.description.data.strip() if form.description.data else None
        event.event_date = form.event_date.data
        event.event_type = form.event_type.data
        db.session.commit()
        log_event("calendar.updated", "academic_calendar", event.id)
        flash("Evento atualizado.", "success")
        return redirect(url_for("admin.calendar"))
    return render_template("admin/calendar_form.html", form=form, title="Editar evento", event=event)

@bp.post("/calendario/<int:event_id>/remover")
@permission_required("calendar.manage")
def calendar_remove(event_id):
    event = db.session.get(AcademicCalendar, event_id)
    if not event:
        abort(404)
    db.session.delete(event)
    db.session.commit()
    log_event("calendar.deleted", "academic_calendar", event_id)
    flash("Evento removido.", "success")
    return redirect(url_for("admin.calendar"))

@bp.get("/academico")
@permission_required("reports.view")
def academic_records():
    rows = Enrollment.query.join(Enrollment.student).join(Enrollment.academic_class).order_by(Enrollment.id.desc()).limit(500).all()
    return render_template("admin/academic_records.html", rows=[(e, calculate_summary(e)) for e in rows])

@bp.get("/usuarios")
@permission_required("users.manage")
def users():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        query = query.filter(or_(User.full_name.ilike(f"%{q}%"), User.username.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    page = max(request.args.get("page", 1, type=int), 1)
    pagination = query.order_by(User.role, User.full_name).paginate(page=page, per_page=25, error_out=False)
    return render_template("admin/users.html", users=pagination.items, pagination=pagination, q=q)


@bp.route("/usuarios/novo-admin", methods=["GET", "POST"])
@permission_required("users.manage")
def admin_new():
    form = UserAdminForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        if User.query.filter(or_(User.username == username, User.email == form.email.data.lower().strip())).first():
            flash("Usuário ou e-mail já cadastrado.", "error")
        else:
            user = User(username=username, email=form.email.data.lower().strip(), full_name=form.full_name.data.strip(), role="admin")
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            db.session.add(Administrator(user_id=user.id))
            db.session.commit()
            log_event("user.created", "administrator", user.id, {"username": user.username})
            flash("Administrador cadastrado.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_admin_form.html", form=form)


@bp.post("/usuarios/<int:user_id>/alternar-status")
@permission_required("users.manage")
def user_toggle(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == g.current_user.id:
        flash("Você não pode desativar o próprio usuário.", "error")
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    user.session_version += 1
    db.session.commit()
    log_event("user.status_changed", "user", user.id, {"active": user.is_active})
    flash("Status do usuário atualizado.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/permissoes", methods=["GET", "POST"])
@permission_required("permissions.manage")
def permissions():
    form = PermissionForm()
    form.user_id.choices = [
        (u.id, f"{u.full_name} — {u.role}")
        for u in User.query.filter(User.role != "admin", User.is_active.is_(True)).order_by(User.full_name).all()
    ]
    form.permission_id.choices = [(p.id, f"{p.code} — {p.name}") for p in Permission.query.order_by(Permission.code).all()]
    if form.validate_on_submit():
        existing = UserPermission.query.filter_by(user_id=form.user_id.data, permission_id=form.permission_id.data).first()
        if existing:
            flash("Essa permissão já está atribuída.", "info")
        else:
            row = UserPermission(user_id=form.user_id.data, permission_id=form.permission_id.data, assigned_by=g.current_user.id)
            db.session.add(row)
            db.session.commit()
            log_event("permission.changed", "user_permission", row.id, {"user_id": row.user_id, "permission_id": row.permission_id})
            flash("Permissão atribuída.", "success")
        return redirect(url_for("admin.permissions"))
    assignments = UserPermission.query.join(UserPermission.user).join(UserPermission.permission).order_by(User.full_name, Permission.code).all()
    return render_template("admin/permissions.html", form=form, assignments=assignments)


@bp.post("/permissoes/<int:assignment_id>/remover")
@permission_required("permissions.manage")
def permission_remove(assignment_id):
    row = db.session.get(UserPermission, assignment_id)
    if not row:
        abort(404)
    db.session.delete(row)
    db.session.commit()
    log_event("permission.changed", "user_permission", assignment_id, {"removed": True})
    flash("Permissão removida.", "success")
    return redirect(url_for("admin.permissions"))


@bp.get("/relatorios")
@permission_required("reports.view")
def reports():
    active_students = Student.query.join(Student.user).filter(User.is_active.is_(True)).count()
    active_teachers = Teacher.query.join(Teacher.user).filter(User.is_active.is_(True)).count()
    current_semester = Semester.query.filter_by(is_current=True).first()
    class_count = AcademicClass.query.filter_by(is_active=True).count()
    enrollment_count = Enrollment.query.filter_by(status="active").count()
    return render_template("admin/reports.html", active_students=active_students, active_teachers=active_teachers, current_semester=current_semester, class_count=class_count, enrollment_count=enrollment_count)


@bp.get("/auditoria")
@permission_required("audit.view")
def audit():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return render_template("admin/audit.html", logs=logs)
