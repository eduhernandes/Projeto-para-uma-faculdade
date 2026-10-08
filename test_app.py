from teofac.extensions import db
from teofac.models import User, Teacher, Student


def login(client, username="admin", password="SenhaForte!123"):
    page = client.get("/auth/login")
    assert page.status_code == 200
    return client.post(
        "/auth/login",
        data={"identifier": username, "password": password, "submit": "Entrar"},
        follow_redirects=False,
    )


def test_home_and_login(client):
    assert client.get("/").status_code == 200
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Entrar" in response.data


def test_invalid_login_is_generic(client, admin):
    response = login(client, password="SenhaErrada!123")
    assert response.status_code == 200
    assert "inválidos".encode("utf-8") in response.data


def test_admin_can_access_admin_route(client, admin):
    response = login(client)
    assert response.status_code == 302
    dashboard = client.get("/admin/")
    assert dashboard.status_code == 200


def test_student_cannot_access_admin_route(app, client):
    with app.app_context():
        student = User(username="aluno", email="aluno@example.test", full_name="Aluno Teste", role="student")
        student.set_password("SenhaForte!123")
        db.session.add(student)
        db.session.flush()
        # The fixture created one course; reuse it without constructing a second record here.
        from teofac.models import Course
        student_profile = Student(user_id=student.id, registration_number="MAT-001", course_id=Course.query.first().id)
        db.session.add(student_profile)
        db.session.commit()
    response = login(client, username="aluno")
    assert response.status_code == 302
    assert client.get("/admin/").status_code == 403


def test_security_headers(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
