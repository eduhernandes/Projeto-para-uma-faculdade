from datetime import date

from teofac.extensions import db
from teofac.models import AcademicClass, Course, Permission, Semester, Student, Subject, Teacher, User, UserPermission


def do_login(client, username, password="SenhaForte!123"):
    return client.post(
        "/auth/login",
        data={"identifier": username, "password": password},
        follow_redirects=False,
    )


def test_student_resource_is_bound_to_session(app, client):
    with app.app_context():
        course = Course.query.first()
        p = Permission(code="student.academic.view", name="Vida acadêmica")
        db.session.add(p)
        db.session.flush()
        for i in (1, 2):
            u = User(username=f"aluno{i}", email=f"aluno{i}@example.test", full_name=f"Aluno {i}", role="student")
            u.set_password("SenhaForte!123")
            db.session.add(u)
            db.session.flush()
            s = Student(user_id=u.id, registration_number=f"MAT-{i}", course_id=course.id)
            db.session.add(s)
            db.session.flush()
            db.session.add(UserPermission(user_id=u.id, permission_id=p.id))
        db.session.commit()
    assert do_login(client, "aluno1").status_code == 302
    response = client.get("/aluno/academico?student_id=2")
    assert response.status_code == 200
    assert b"Aluno 2" not in response.data


def test_teacher_cannot_open_another_teacher_class(app, client):
    with app.app_context():
        course = Course.query.first()
        semester = Semester(code="2026.2", name="2026.2", start_date=date(2026, 7, 1), end_date=date(2026, 12, 31))
        db.session.add(semester)
        p = Permission(code="teacher.classes.view", name="Turmas")
        db.session.add(p)
        t1 = User(username="prof1", email="prof1@example.test", full_name="Professor 1", role="teacher")
        t1.set_password("SenhaForte!123")
        t2 = User(username="prof2", email="prof2@example.test", full_name="Professor 2", role="teacher")
        t2.set_password("SenhaForte!123")
        db.session.add_all([t1, t2])
        db.session.flush()
        teacher1 = Teacher(user_id=t1.id, employee_number="PROF-1")
        teacher2 = Teacher(user_id=t2.id, employee_number="PROF-2")
        db.session.add_all([teacher1, teacher2])
        subject = Subject(course_id=course.id, code="DIR001", name="Introdução à Teologia", workload_hours=60, semester_number=1)
        db.session.add(subject)
        db.session.flush()
        c1 = AcademicClass(subject_id=subject.id, semester_id=semester.id, teacher_id=teacher1.id, code="T1")
        c2 = AcademicClass(subject_id=subject.id, semester_id=semester.id, teacher_id=teacher2.id, code="T2")
        db.session.add_all([c1, c2])
        db.session.flush()
        db.session.add(UserPermission(user_id=t1.id, permission_id=p.id))
        db.session.commit()
    assert do_login(client, "prof1").status_code == 302
    assert client.get(f"/professor/turmas/{c2.id}").status_code == 403
