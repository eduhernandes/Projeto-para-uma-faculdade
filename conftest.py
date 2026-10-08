import pytest
from teofac import create_app
from teofac.extensions import db
from teofac.models import Course, User

@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        course = Course(code="TEO", name="Bacharelado em Teologia", duration_semesters=8)
        db.session.add(course)
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def admin(app):
    with app.app_context():
        user = User(username="admin", email="admin@example.test", full_name="Administrador", role="admin")
        user.set_password("SenhaForte!123")
        db.session.add(user)
        db.session.commit()
        return user
