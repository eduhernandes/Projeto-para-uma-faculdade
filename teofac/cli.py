import getpass
import re
import click
from flask import current_app
from flask.cli import with_appcontext

from .extensions import db
from .models import Administrator, User
from .services.permissions import seed_permissions


def register_commands(app):
    @app.cli.command("init-db")
    @with_appcontext
    def init_db():
        """Cria as tabelas diretamente; para ambientes versionados, prefira `flask db upgrade`."""
        db.create_all()
        seed_permissions()
        click.echo("Banco inicializado e permissões padrão verificadas.")

    @app.cli.command("seed-permissions")
    @with_appcontext
    def seed_permissions_command():
        seed_permissions()
        click.echo("Permissões padrão atualizadas.")

    @app.cli.command("create-admin")
    @with_appcontext
    def create_admin():
        """Cria o primeiro administrador solicitando a senha de forma interativa."""
        username = click.prompt("Usuário").strip().lower()
        email = click.prompt("E-mail").strip().lower()
        full_name = click.prompt("Nome completo")
        if User.query.filter((User.username == username) | (User.email == email)).first():
            raise click.ClickException("Usuário ou e-mail já cadastrado.")
        password = getpass.getpass("Senha (não será exibida): ")
        confirm = getpass.getpass("Confirme a senha: ")
        if password != confirm:
            raise click.ClickException("As senhas não coincidem.")
        if len(password) < 12 or len(password) > 128 or not (re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"\d", password) and re.search(r"[^A-Za-z0-9]", password)):
            raise click.ClickException("A senha deve ter 12–128 caracteres e conter maiúscula, minúscula, número e caractere especial.")
        user = User(username=username, email=email, full_name=full_name.strip(), role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        db.session.add(Administrator(user_id=user.id))
        db.session.commit()
        click.echo(f"Administrador criado com ID {user.id}.")
