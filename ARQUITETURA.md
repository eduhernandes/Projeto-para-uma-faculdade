# Arquitetura do TéoFac Acadêmico

## 1. Arquitetura do sistema

A aplicação usa Application Factory + Blueprints. A entrada é `run.py` em desenvolvimento e `wsgi.py` em produção. O domínio é dividido por responsabilidades:

- **Blueprints:** rotas e fluxos de cada perfil.
- **Models:** entidades e relacionamentos SQLAlchemy.
- **Services:** regras de autenticação, auditoria, permissões e cálculo acadêmico.
- **Forms:** validação server-side e CSRF.
- **Templates:** apresentação em Jinja2.
- **Static:** CSS3 e JavaScript.
- **Config:** desenvolvimento, testes e produção.

A decisão reduz o acoplamento de `app.py`, permite testar serviços isoladamente e deixa o caminho aberto para PostgreSQL.

## 2. Estrutura de pastas

```text
teofac/
├── blueprints/        # HTTP e autorização de cada área
├── services/          # regras de negócio reutilizáveis
├── templates/         # Jinja2
├── static/            # CSS/JS
├── models.py          # modelo relacional
├── forms.py           # validação e CSRF
├── decorators.py      # autorização no servidor
├── config.py          # ambientes
├── extensions.py      # SQLAlchemy, Migrate, CSRF e Limiter
└── cli.py             # inicialização e comandos administrativos
```

## 3. Modelo do banco

| Tabela | Finalidade |
|---|---|
| users | autenticação, perfil, estado da conta e versão de sessão |
| students | dados acadêmicos do aluno |
| teachers | dados funcionais do professor |
| administrators | especialização administrativa |
| courses | cursos |
| semesters | períodos e regras acadêmicas |
| subjects | disciplinas de cada curso |
| classes | oferta de disciplina em um período |
| enrollments | matrícula aluno ↔ turma |
| assessments | avaliações de uma turma |
| grades | nota de um aluno em uma avaliação |
| attendance | presença/falta por aluno e data |
| academic_calendar | eventos acadêmicos |
| permissions | catálogo de permissões |
| user_permissions | associação usuário ↔ permissão |
| audit_logs | trilha de auditoria |
| password_reset_tokens | suporte a recuperação de senha |

## 4. Relacionamentos

```text
users 1──1 students ──N enrollments N──1 classes N──1 subjects N──1 courses
users 1──1 teachers ──N classes
semesters 1──N classes
classes 1──N assessments 1──N grades N──1 enrollments
classes/enrollments 1──N attendance
semesters 1──N academic_calendar
users N──N permissions (via user_permissions)
users 1──N audit_logs
users 1──N password_reset_tokens
```

As chaves estrangeiras, restrições únicas e checks reduzem inconsistências estruturais; o SQLite recebe `PRAGMA foreign_keys=ON`.

## 5. Autenticação

1. Usuário envia identificador e senha por formulário protegido por CSRF.
2. O servidor normaliza o identificador e busca o usuário pelo ORM.
3. A senha é validada contra o hash `scrypt`.
4. A sessão é limpa antes do login para dificultar session fixation.
5. A sessão recebe `user_id`, `session_version`, hash do user-agent e instante de emissão.
6. Em cada requisição, o servidor recarrega o usuário e verifica estado ativo, versão de sessão e user-agent.
7. Logout limpa a sessão.

A expiração da sessão é configurável por ambiente.

## 6. Autorização

Há duas camadas:

- `role_required(...)` para garantir o perfil.
- `permission_required(...)` para garantir a capacidade específica.

Autorização por recurso é aplicada dentro da view, não apenas na interface. Exemplo: o professor só consegue acessar uma turma quando o `teacher_id` da turma é o mesmo do professor autenticado.

No fluxo de aluno, o `student_id` não é obtido da URL: o servidor usa a relação do usuário autenticado. Isso impede que a troca manual de um ID revele dados de outro aluno.

## 7. Segurança

- Senhas com `scrypt`, nunca texto puro.
- `.env` para secrets.
- Cookie `HttpOnly` e `SameSite=Lax`; `Secure=True` em produção.
- CSRF global para formulários Flask-WTF.
- Rate limiting específico no login.
- SQLAlchemy ORM e parâmetros gerados pelo framework.
- CSP e headers de segurança.
- Erros genéricos para o usuário e detalhes apenas no log do servidor.
- Auditoria de login, alterações de usuários, permissões, notas, frequência e operações administrativas.
- Nenhum upload habilitado na primeira versão.

### Limitações conscientes da primeira versão

O armazenamento de rate limiting padrão é `memory://`, suficiente para desenvolvimento local, mas inadequado para múltiplos processos/instâncias. Em produção deve ser trocado por um armazenamento compartilhado. A sessão atual é baseada no cookie assinado padrão do Flask; ela não é armazenamento server-side. A defesa contra roubo de sessão usa expiração, HttpOnly, SameSite, versão de sessão e verificação do user-agent, mas um ambiente de alta segurança pode evoluir para um gerenciador de sessões server-side e MFA.

## 8. Escalabilidade

A persistência usa SQLAlchemy em vez de SQL específico do SQLite. A configuração já separa `DATABASE_URL`, então a migração para PostgreSQL pode ocorrer mantendo o mesmo modelo de domínio e revisando as migrations. O WSGI de produção já está isolado do servidor de desenvolvimento.
