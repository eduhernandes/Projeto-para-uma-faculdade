import re
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, FloatField, IntegerField, PasswordField, SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, Regexp, ValidationError

def validate_password_strength(form,field):
    v=field.data or ''
    if len(v)<12 or len(v)>128: raise ValidationError('A senha deve ter entre 12 e 128 caracteres.')
    if not(re.search(r'[A-Z]',v) and re.search(r'[a-z]',v) and re.search(r'\d',v) and re.search(r'[^A-Za-z0-9]',v)): raise ValidationError('Use maiúscula, minúscula, número e caractere especial.')
class LoginForm(FlaskForm):
    identifier=StringField('Usuário ou e-mail',validators=[DataRequired(),Length(max=255)]); password=PasswordField('Senha',validators=[DataRequired(),Length(max=128)]); submit=SubmitField('Entrar')
class ConfirmForm(FlaskForm): submit=SubmitField('Confirmar')
class StudentForm(FlaskForm):
    full_name=StringField('Nome completo',validators=[DataRequired(),Length(min=3,max=180)]); username=StringField('Usuário',validators=[DataRequired(),Length(min=3,max=80),Regexp(r'^[A-Za-z0-9._-]+$', message='Use apenas letras, números, ponto, hífen ou sublinhado.')]); email=StringField('E-mail',validators=[DataRequired(),Email(),Length(max=255)]); registration_number=StringField('Matrícula',validators=[DataRequired(),Length(min=2,max=50)]); course_id=SelectField('Curso',coerce=int,validators=[DataRequired()]); birth_date=DateField('Data de nascimento',validators=[Optional()]); phone=StringField('Telefone',validators=[Optional(),Length(max=30)]); address=StringField('Endereço',validators=[Optional(),Length(max=300)]); password=PasswordField('Senha',validators=[Optional(),validate_password_strength]); submit=SubmitField('Salvar')
class TeacherForm(FlaskForm):
    full_name=StringField('Nome completo',validators=[DataRequired(),Length(min=3,max=180)]); username=StringField('Usuário',validators=[DataRequired(),Length(min=3,max=80),Regexp(r'^[A-Za-z0-9._-]+$', message='Use apenas letras, números, ponto, hífen ou sublinhado.')]); email=StringField('E-mail',validators=[DataRequired(),Email(),Length(max=255)]); employee_number=StringField('Registro funcional',validators=[DataRequired(),Length(min=2,max=50)]); specialization=StringField('Especialidade',validators=[Optional(),Length(max=180)]); password=PasswordField('Senha',validators=[Optional(),validate_password_strength]); submit=SubmitField('Salvar')
class AdminUserForm(FlaskForm):
    full_name=StringField('Nome completo',validators=[DataRequired(),Length(min=3,max=180)]); username=StringField('Usuário',validators=[DataRequired(),Length(min=3,max=80),Regexp(r'^[A-Za-z0-9._-]+$', message='Use apenas letras, números, ponto, hífen ou sublinhado.')]); email=StringField('E-mail',validators=[DataRequired(),Email(),Length(max=255)]); password=PasswordField('Senha',validators=[DataRequired(),validate_password_strength]); is_active=BooleanField('Usuário ativo',default=True); submit=SubmitField('Salvar')
class CourseForm(FlaskForm):
    code=StringField('Código',validators=[DataRequired(),Length(min=2,max=30)]); name=StringField('Nome',validators=[DataRequired(),Length(min=3,max=180)]); description=TextAreaField('Descrição',validators=[Optional(),Length(max=3000)]); duration_semesters=IntegerField('Duração (semestres)',validators=[DataRequired(),NumberRange(min=1,max=30)]); is_active=BooleanField('Ativo',default=True); submit=SubmitField('Salvar')
class SubjectForm(FlaskForm):
    course_id=SelectField('Curso',coerce=int,validators=[DataRequired()]); code=StringField('Código',validators=[DataRequired(),Length(min=2,max=30)]); name=StringField('Nome',validators=[DataRequired(),Length(min=3,max=180)]); workload_hours=IntegerField('Carga horária',validators=[DataRequired(),NumberRange(min=1,max=1000)]); semester_number=IntegerField('Semestre do curso',validators=[DataRequired(),NumberRange(min=1,max=30)]); is_active=BooleanField('Ativa',default=True); submit=SubmitField('Salvar')
class SemesterForm(FlaskForm):
    code=StringField('Código',validators=[DataRequired(),Length(min=2,max=30)]); name=StringField('Nome',validators=[DataRequired(),Length(min=3,max=120)]); start_date=DateField('Início',validators=[DataRequired()]); end_date=DateField('Fim',validators=[DataRequired()]); is_current=BooleanField('Período atual'); minimum_average=FloatField('Média mínima',validators=[DataRequired(),NumberRange(min=0,max=10)]); minimum_attendance_pct=FloatField('Frequência mínima (%)',validators=[DataRequired(),NumberRange(min=0,max=100)]); maximum_absences=IntegerField('Máximo de faltas',validators=[Optional(),NumberRange(min=0,max=1000)]); number_of_assessments=IntegerField('Número de avaliações',validators=[Optional(),NumberRange(min=1,max=100)]); recovery_enabled=BooleanField('Permitir recuperação'); submit=SubmitField('Salvar')
    def validate_end_date(self,f):
        if self.start_date.data and f.data and f.data<self.start_date.data: raise ValidationError('A data final deve ser posterior ou igual à inicial.')
class ClassForm(FlaskForm):
    subject_id=SelectField('Disciplina',coerce=int,validators=[DataRequired()]); semester_id=SelectField('Período letivo',coerce=int,validators=[DataRequired()]); teacher_id=SelectField('Professor',coerce=int,validators=[Optional()]); code=StringField('Código da turma',validators=[DataRequired(),Length(min=2,max=50)]); room=StringField('Sala',validators=[Optional(),Length(max=50)]); weekday=SelectField('Dia da semana',coerce=int,choices=[(0,'Segunda'),(1,'Terça'),(2,'Quarta'),(3,'Quinta'),(4,'Sexta'),(5,'Sábado'),(6,'Domingo')],validators=[Optional()]); start_time=TimeField('Início',format='%H:%M',validators=[Optional()]); end_time=TimeField('Fim',format='%H:%M',validators=[Optional()]); is_active=BooleanField('Ativa',default=True); submit=SubmitField('Salvar')
    def validate_end_time(self,f):
        if self.start_time.data and f.data and f.data<=self.start_time.data: raise ValidationError('O horário final deve ser posterior ao inicial.')
class CalendarForm(FlaskForm):
    semester_id=SelectField('Período letivo',coerce=int,validators=[DataRequired()]); title=StringField('Título',validators=[DataRequired(),Length(min=3,max=180)]); description=TextAreaField('Descrição',validators=[Optional(),Length(max=3000)]); event_date=DateField('Data',validators=[DataRequired()]); event_type=SelectField('Tipo',choices=[('geral','Geral'),('prova','Prova'),('feriado','Feriado'),('recesso','Recesso'),('academico','Acadêmico')],validators=[DataRequired()]); submit=SubmitField('Salvar')
class EnrollmentForm(FlaskForm):
    student_id=SelectField('Aluno',coerce=int,validators=[DataRequired()]); submit=SubmitField('Matricular')
class AssessmentForm(FlaskForm):
    title=StringField('Avaliação',validators=[DataRequired(),Length(min=2,max=180)]); assessment_date=DateField('Data',validators=[DataRequired()]); max_score=FloatField('Nota máxima',validators=[DataRequired(),NumberRange(min=.01,max=1000)]); weight=FloatField('Peso',validators=[DataRequired(),NumberRange(min=.01,max=100)]); submit=SubmitField('Criar avaliação')
class GradeForm(FlaskForm): score=FloatField('Nota',validators=[DataRequired(),NumberRange(min=0,max=1000)]); submit=SubmitField('Salvar nota')
class AttendanceForm(FlaskForm): attendance_date=DateField('Data da frequência',validators=[DataRequired()]); submit=SubmitField('Salvar frequência')
class PermissionForm(FlaskForm):
    user_id=SelectField('Usuário',coerce=int,validators=[DataRequired()])
    permission_id=SelectField('Permissão',coerce=int,validators=[DataRequired()])
    submit=SubmitField('Atribuir permissão')

# Aliases semânticos usados pelos Blueprints
AcademicClassForm = ClassForm
AcademicEventForm = CalendarForm
UserAdminForm = AdminUserForm
