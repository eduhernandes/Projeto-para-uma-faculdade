# TéoFac Acadêmico

Sistema web de gestão acadêmica e administrativa para uma faculdade teológica, construído com Python, Flask, SQLite, HTML5, CSS3, JavaScript e Jinja2.

## 1. Pré-requisitos

- Python 3.11+ instalado.
- VS Code.
- Terminal com PowerShell, CMD, Bash ou equivalente.

## 2. Criar o ambiente virtual

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
py -3 -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Instalar dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configurar o `.env`

Copie `.env.example` para `.env` e substitua `SECRET_KEY` por um valor aleatório forte.

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash:

```bash
cp .env.example .env
```

Na primeira versão, o banco padrão é `sqlite:///teologia.db`, armazenado na pasta `instance/`.

## 5. Criar o banco

Para o fluxo versionado por migrations:

```bash
flask --app run:app db upgrade
```

Depois, garanta as permissões padrão:

```bash
flask --app run:app seed-permissions
```

Para uma inicialização rápida sem migration existente, também existe:

```bash
flask --app run:app init-db
```

### Banco de teste populado

Crie ou atualize o banco SQLite local com dados de demonstração:

```bash
python init_test_db.py
```

O script usa uma configuração isolada e grava em `instance/test_teologia.db`, sem alterar o banco principal configurado em `.env`. Pode ser executado novamente sem duplicar os registros de demonstração. O arquivo do banco é local e está excluído do Git.

Para iniciar a aplicação usando esse banco no PowerShell:

```powershell
$env:FLASK_ENV = "testdb"
flask --app run:app run --debug
```

Para voltar ao banco definido no `.env`, feche o servidor e remova a variável na sessão atual:

```powershell
Remove-Item Env:FLASK_ENV
```

Contas de demonstração:

| Perfil | Usuário | Senha |
|---|---|---|
| Administrador | `admin.demo` | `AdminDemo!2026` |
| Professor | `professor.demo` | `ProfessorDemo!2026` |
| Aluno | `aluno.demo` | `AlunoDemo!2026` |

Essas credenciais são apenas para desenvolvimento local; não as reutilize em produção.

## 6. Criar o primeiro administrador

Não existe senha administrativa fixa no código. Crie o administrador interativamente:

```bash
flask --app run:app create-admin
```

O terminal solicitará usuário, e-mail, nome e senha. A senha é convertida em hash `scrypt` antes de ser armazenada.

## 7. Iniciar o sistema

Para desenvolvimento local:

```bash
python run.py
```

ou:

```bash
flask --app run:app run --debug
```

Acesse `http://127.0.0.1:5000`.

## 8. Perfis

### Administrador

Gerencia alunos, professores, cursos, disciplinas, períodos, turmas, matrículas, calendário, usuários, permissões, relatórios e auditoria.

### Professor

Visualiza somente suas turmas, alunos dessas turmas, avaliações, notas, frequência, calendário e o histórico acadêmico necessário relacionado às suas turmas.

### Aluno

Visualiza somente os próprios dados, disciplinas, turmas, notas, avaliações, médias, faltas, frequência, situação acadêmica, horário, calendário e histórico.

## 9. Segurança

O projeto foi organizado com as regras de segurança como parte da arquitetura:

- Hash de senha forte com `scrypt`.
- Sessão servidor-side via cookie assinado, com versão de sessão, identificação do user-agent e expiração.
- Rotas protegidas por perfil e permissão no servidor.
- Professor só acessa uma turma quando `class.teacher_id` corresponde ao seu perfil.
- Aluno nunca recebe `student_id` para escolher quem consultar; o servidor deriva o aluno da sessão.
- CSRF habilitado para formulários.
- Limitação de login: 5 tentativas por 15 minutos por origem.
- SQLAlchemy ORM para evitar SQL montado com dados do navegador.
- CSP, `HttpOnly`, `SameSite`, `X-Content-Type-Options`, `X-Frame-Options`, política de referrer e HSTS em produção.
- Logs de auditoria sem senha, tokens ou segredos.
- Erros internos são registrados no log do servidor e não são expostos ao usuário.
- Uploads não são habilitados nesta primeira versão.

## 10. Recuperação de senha

O modelo `password_reset_tokens` e os serviços de criação/consumo do token já estão preparados. O envio por e-mail e a interface final de redefinição dependem da futura configuração de um provedor de e-mail.

## 11. Migrations

Gerar uma migration depois de alterar models:

```bash
flask --app run:app db migrate -m "descreva a mudança"
flask --app run:app db upgrade
```

Antes de produção, revise migrations manualmente e teste restauração de backup.

## 12. Produção

Não use `python run.py`/servidor de desenvolvimento como servidor público definitivo. O ponto de entrada WSGI está em `wsgi.py`:

```python
from teofac import create_app
application = create_app("production")
```

A implantação futura deve considerar um servidor WSGI, HTTPS, PostgreSQL, secrets por ambiente, armazenamento compartilhado para rate limiting, backup, monitoramento e rotação de logs.

Para PostgreSQL, basta fornecer uma `DATABASE_URL` compatível e verificar as migrations antes da troca. O código de persistência usa SQLAlchemy para reduzir o acoplamento ao SQLite.

## 13. Estrutura do projeto

```text
teologia_academico/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
├── wsgi.py
├── migrations/
├── instance/
├── docs/
├── tests/
└── teofac/
    ├── __init__.py
    ├── cli.py
    ├── config.py
    ├── decorators.py
    ├── extensions.py
    ├── forms.py
    ├── models.py
    ├── blueprints/
    ├── services/
    ├── templates/
    │   ├── admin/
    │   ├── auth/
    │   ├── dashboards/
    │   ├── errors/
    │   ├── student/
    │   └── teacher/
    └── static/
```

`blueprints/` separa as áreas funcionais; `models.py` representa o domínio relacional; `services/` concentra autenticação, auditoria e regras acadêmicas; `forms.py` concentra validação de entrada; `templates/` contém a camada Jinja2; `static/` contém CSS/JS; `config.py` separa ambientes; `migrations/` versiona alterações do banco; `tests/` concentra testes automatizados.

## 14. Regras acadêmicas

O período letivo armazena média mínima, frequência mínima, limite de faltas, número esperado de avaliações e indicação de recuperação. A situação acadêmica é calculada pelo serviço `teofac/services/academic.py`, evitando que essas regras fiquem fixadas em cada tela.

A primeira implementação calcula a média a partir das notas lançadas e a frequência a partir dos registros de presença/falta. Avaliações já têm campo `weight` para evolução posterior para média ponderada.

## 15. Próximas evoluções recomendadas

- Integração de e-mail para recuperação de senha.
- MFA/2FA.
- PostgreSQL.
- Redis ou outro armazenamento compartilhado para rate limiting.
- Backup automatizado e testes de restauração.
- Relatórios exportáveis.
- Workflow de recuperação/provas finais.
- Permissões ainda mais granulares por operação.
- Observabilidade, métricas e alertas.
