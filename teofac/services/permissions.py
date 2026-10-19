from ..extensions import db
from ..models import Permission, UserPermission


DEFAULT_PERMISSIONS = {
    "admin": [
        "admin.dashboard", "students.manage", "teachers.manage", "courses.manage", "subjects.manage",
        "semesters.manage", "classes.manage", "enrollments.manage", "calendar.manage", "users.manage",
        "permissions.manage", "reports.view", "audit.view",
    ],
    "teacher": ["teacher.classes.view", "teacher.grades.write", "teacher.attendance.write", "teacher.calendar.view", "teacher.history.view"],
    "student": ["student.academic.view", "student.calendar.view"],
}

PERMISSION_META = {
    "admin.dashboard": ("Painel administrativo", "Acesso ao painel do administrador."),
    "students.manage": ("Gerenciar alunos", "Criar, editar e desativar alunos."),
    "teachers.manage": ("Gerenciar professores", "Criar, editar e desativar professores."),
    "courses.manage": ("Gerenciar cursos", "Criar e editar cursos."),
    "subjects.manage": ("Gerenciar disciplinas", "Criar e editar disciplinas."),
    "semesters.manage": ("Gerenciar períodos", "Criar e editar períodos letivos e regras."),
    "classes.manage": ("Gerenciar turmas", "Criar e editar turmas e vínculos de professor."),
    "enrollments.manage": ("Gerenciar matrículas", "Matricular e remover alunos de turmas."),
    "calendar.manage": ("Gerenciar calendário", "Criar eventos acadêmicos."),
    "users.manage": ("Gerenciar usuários", "Gerenciar usuários e administradores."),
    "permissions.manage": ("Gerenciar permissões", "Atribuir permissões granulares."),
    "reports.view": ("Visualizar relatórios", "Acesso aos indicadores administrativos."),
    "audit.view": ("Visualizar auditoria", "Acesso aos registros de auditoria."),
    "teacher.classes.view": ("Professor: turmas", "Visualizar turmas vinculadas ao professor."),
    "teacher.grades.write": ("Professor: notas", "Criar avaliações e lançar/alterar notas."),
    "teacher.attendance.write": ("Professor: frequência", "Lançar e alterar frequência das turmas próprias."),
    "teacher.calendar.view": ("Professor: calendário", "Visualizar calendário dos períodos vinculados."),
    "teacher.history.view": ("Professor: histórico", "Visualizar histórico acadêmico necessário de seus alunos."),
    "student.academic.view": ("Aluno: vida acadêmica", "Visualizar notas, médias e frequência próprias."),
    "student.calendar.view": ("Aluno: calendário", "Visualizar calendário acadêmico relacionado às próprias matrículas."),
}


def seed_permissions():
    for code, (name, description) in PERMISSION_META.items():
        item = Permission.query.filter_by(code=code).first()
        if not item:
            db.session.add(Permission(code=code, name=name, description=description))
    db.session.commit()


def grant_role_permissions(user):
    seed_permissions()
    codes = DEFAULT_PERMISSIONS.get(user.role, [])
    permissions = {
        permission.code: permission
        for permission in Permission.query.filter(Permission.code.in_(codes)).all()
    }
    for code in codes:
        permission = permissions.get(code)
        if permission and not UserPermission.query.filter_by(
            user_id=user.id, permission_id=permission.id
        ).first():
            db.session.add(UserPermission(user_id=user.id, permission_id=permission.id))
    db.session.commit()
