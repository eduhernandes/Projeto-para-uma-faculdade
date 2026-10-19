from datetime import date, time
from pathlib import Path

from teofac import create_app
from teofac.extensions import db
from teofac.models import (
    AcademicCalendar,
    AcademicClass,
    Administrator,
    Assessment,
    Attendance,
    Course,
    Enrollment,
    Grade,
    Semester,
    Student,
    Subject,
    Teacher,
    User,
)
from teofac.services.permissions import grant_role_permissions, seed_permissions


DEMO_PASSWORDS = {
    "admin": "AdminDemo!2026",
    "professor": "ProfessorDemo!2026",
    "aluno": "AlunoDemo!2026",
}


def get_or_create(model, *, defaults=None, **filters):
    instance = model.query.filter_by(**filters).first()
    if instance is None:
        instance = model(**filters, **(defaults or {}))
        db.session.add(instance)
        db.session.flush()
    return instance


def seed_test_data():
    db.create_all()
    seed_permissions()

    course = get_or_create(
        Course,
        code="DEMO-TEO",
        name="Bacharelado de demonstração em Teologia",
    )
    course.duration_semesters = 8
    course.is_active = True

    semester = get_or_create(
        Semester,
        code="2026.2",
        defaults={
            "name": "Segundo semestre de 2026",
            "start_date": date(2026, 7, 1),
            "end_date": date(2026, 12, 20),
        },
    )
    semester.name = "Segundo semestre de 2026"
    semester.start_date = date(2026, 7, 1)
    semester.end_date = date(2026, 12, 20)
    semester.is_current = True
    semester.minimum_average = 6.0
    semester.minimum_attendance_pct = 75.0
    semester.maximum_absences = 5
    semester.number_of_assessments = 2
    semester.recovery_enabled = True

    admin = get_or_create(
        User,
        username="admin.demo",
        defaults={
            "email": "admin.demo@example.test",
            "full_name": "Administradora de demonstração",
            "role": "admin",
            "password_hash": "temporary",
        },
    )
    admin.email = "admin.demo@example.test"
    admin.full_name = "Administradora de demonstração"
    admin.role = "admin"
    admin.is_active = True
    admin.set_password(DEMO_PASSWORDS["admin"])
    get_or_create(Administrator, user_id=admin.id)

    teacher_user = get_or_create(
        User,
        username="professor.demo",
        defaults={
            "email": "professor.demo@example.test",
            "full_name": "Professora de demonstração",
            "role": "teacher",
            "password_hash": "temporary",
        },
    )
    teacher_user.email = "professor.demo@example.test"
    teacher_user.full_name = "Professora de demonstração"
    teacher_user.role = "teacher"
    teacher_user.is_active = True
    teacher_user.set_password(DEMO_PASSWORDS["professor"])
    teacher = get_or_create(
        Teacher,
        user_id=teacher_user.id,
        defaults={"employee_number": "DOC-DEMO-001"},
    )
    teacher.employee_number = "DOC-DEMO-001"
    teacher.specialization = "História da Teologia"

    student_user = get_or_create(
        User,
        username="aluno.demo",
        defaults={
            "email": "aluno.demo@example.test",
            "full_name": "Aluno de demonstração",
            "role": "student",
            "password_hash": "temporary",
        },
    )
    student_user.email = "aluno.demo@example.test"
    student_user.full_name = "Aluno de demonstração"
    student_user.role = "student"
    student_user.is_active = True
    student_user.set_password(DEMO_PASSWORDS["aluno"])
    student = get_or_create(
        Student,
        user_id=student_user.id,
        defaults={"registration_number": "MAT-DEMO-001", "course_id": course.id},
    )
    student.registration_number = "MAT-DEMO-001"
    student.course_id = course.id
    student.birth_date = date(2000, 5, 15)
    student.phone = "(11) 99999-0001"

    subject = get_or_create(
        Subject,
        code="DEMO101",
        defaults={
            "course_id": course.id,
            "name": "Introdução à Teologia",
        },
    )
    subject.course_id = course.id
    subject.name = "Introdução à Teologia"
    subject.workload_hours = 60
    subject.semester_number = 1
    subject.is_active = True

    academic_class = get_or_create(
        AcademicClass,
        code="DEMO-2026-2-A",
        defaults={
            "subject_id": subject.id,
            "semester_id": semester.id,
        },
    )
    academic_class.subject_id = subject.id
    academic_class.semester_id = semester.id
    academic_class.teacher_id = teacher.id
    academic_class.room = "Sala 01"
    academic_class.weekday = 2
    academic_class.start_time = time(19, 0)
    academic_class.end_time = time(20, 30)
    academic_class.is_active = True

    enrollment = get_or_create(
        Enrollment,
        student_id=student.id,
        class_id=academic_class.id,
    )
    enrollment.status = "active"

    assessments = []
    for title, assessment_date, weight in (
        ("Avaliação parcial", date(2026, 9, 15), 1.0),
        ("Trabalho final", date(2026, 11, 10), 1.0),
    ):
        assessment = get_or_create(
            Assessment,
            class_id=academic_class.id,
            title=title,
            defaults={
                "assessment_date": assessment_date,
                "max_score": 10.0,
                "weight": weight,
            },
        )
        assessment.assessment_date = assessment_date
        assessment.max_score = 10.0
        assessment.weight = weight
        assessments.append(assessment)

    for assessment, score in zip(assessments, (8.5, 9.0)):
        grade = get_or_create(
            Grade,
            assessment_id=assessment.id,
            enrollment_id=enrollment.id,
            defaults={"score": score, "entered_by": teacher_user.id},
        )
        grade.score = score
        grade.entered_by = teacher_user.id

    for attendance_date, status in (
        (date(2026, 8, 4), "present"),
        (date(2026, 8, 11), "present"),
        (date(2026, 8, 18), "absent"),
        (date(2026, 8, 25), "present"),
    ):
        attendance = get_or_create(
            Attendance,
            enrollment_id=enrollment.id,
            attendance_date=attendance_date,
            defaults={"status": status, "recorded_by": teacher_user.id},
        )
        attendance.status = status
        attendance.recorded_by = teacher_user.id

    event = get_or_create(
        AcademicCalendar,
        semester_id=semester.id,
        title="Semana de avaliações",
        event_date=date(2026, 11, 9),
    )
    event.description = "Período de avaliações e atividades de encerramento."
    event.event_type = "avaliacao"

    db.session.commit()
    grant_role_permissions(teacher_user)
    grant_role_permissions(student_user)


def main():
    app = create_app("testdb")
    with app.app_context():
        seed_test_data()
        database_path = Path(app.instance_path) / "test_teologia.db"
        print(f"Banco de teste inicializado: {database_path}")
        print("Contas de demonstração (somente para desenvolvimento local):")
        for username, password in DEMO_PASSWORDS.items():
            print(f"  {username}: {password}")


if __name__ == "__main__":
    main()
