from datetime import datetime, timezone
from secrets import token_hex
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db

def utcnow(): return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80),unique=True,nullable=False,index=True)
    email=db.Column(db.String(255),unique=True,nullable=False,index=True); full_name=db.Column(db.String(180),nullable=False)
    password_hash=db.Column(db.String(255),nullable=False); role=db.Column(db.String(20),nullable=False,index=True)
    is_active=db.Column(db.Boolean,nullable=False,default=True,index=True); session_version=db.Column(db.String(64),nullable=False,default='1')
    __table_args__=(db.CheckConstraint("role IN ('admin','teacher','student')",name='ck_users_role'),)
    last_login_at=db.Column(db.DateTime(timezone=True)); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow); updated_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow,onupdate=utcnow)
    student=db.relationship('Student',back_populates='user',uselist=False,cascade='all, delete-orphan'); teacher=db.relationship('Teacher',back_populates='user',uselist=False,cascade='all, delete-orphan'); administrator=db.relationship('Administrator',back_populates='user',uselist=False,cascade='all, delete-orphan'); permissions=db.relationship('UserPermission',foreign_keys='UserPermission.user_id',back_populates='user',cascade='all, delete-orphan')
    def has_permission(self,code): return self.role=='admin' or any(p.permission.code==code for p in self.permissions)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")
        self.session_version = token_hex(16)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__='students'
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='CASCADE'),unique=True,nullable=False); registration_number=db.Column(db.String(50),unique=True,nullable=False,index=True); course_id=db.Column(db.Integer,db.ForeignKey('courses.id',ondelete='RESTRICT'),nullable=False,index=True); birth_date=db.Column(db.Date); phone=db.Column(db.String(30)); address=db.Column(db.String(300)); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    user=db.relationship('User',back_populates='student'); course=db.relationship('Course',back_populates='students'); enrollments=db.relationship('Enrollment',back_populates='student',cascade='all, delete-orphan')

class Teacher(db.Model):
    __tablename__='teachers'
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='CASCADE'),unique=True,nullable=False); employee_number=db.Column(db.String(50),unique=True,nullable=False,index=True); specialization=db.Column(db.String(180)); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    user=db.relationship('User',back_populates='teacher'); classes=db.relationship('AcademicClass',back_populates='teacher')

class Administrator(db.Model):
    __tablename__='administrators'
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='CASCADE'),unique=True,nullable=False); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    user=db.relationship('User',back_populates='administrator')

class Course(db.Model):
    __tablename__='courses'
    id=db.Column(db.Integer,primary_key=True); code=db.Column(db.String(30),unique=True,nullable=False,index=True); name=db.Column(db.String(180),nullable=False); description=db.Column(db.Text); duration_semesters=db.Column(db.Integer,nullable=False,default=8); is_active=db.Column(db.Boolean,nullable=False,default=True,index=True); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow); updated_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow,onupdate=utcnow)
    students=db.relationship('Student',back_populates='course'); subjects=db.relationship('Subject',back_populates='course',cascade='all, delete-orphan')

class Semester(db.Model):
    __tablename__='semesters'
    id=db.Column(db.Integer,primary_key=True); code=db.Column(db.String(30),unique=True,nullable=False,index=True); name=db.Column(db.String(120),nullable=False); start_date=db.Column(db.Date,nullable=False); end_date=db.Column(db.Date,nullable=False); is_current=db.Column(db.Boolean,nullable=False,default=False,index=True); minimum_average=db.Column(db.Float,nullable=False,default=6.0); minimum_attendance_pct=db.Column(db.Float,nullable=False,default=75.0); maximum_absences=db.Column(db.Integer); number_of_assessments=db.Column(db.Integer); recovery_enabled=db.Column(db.Boolean,nullable=False,default=False); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    classes=db.relationship('AcademicClass',back_populates='semester'); events=db.relationship('AcademicCalendar',back_populates='semester',cascade='all, delete-orphan')

class Subject(db.Model):
    __tablename__='subjects'
    id=db.Column(db.Integer,primary_key=True); course_id=db.Column(db.Integer,db.ForeignKey('courses.id',ondelete='RESTRICT'),nullable=False,index=True); code=db.Column(db.String(30),unique=True,nullable=False,index=True); name=db.Column(db.String(180),nullable=False); workload_hours=db.Column(db.Integer,nullable=False,default=60); semester_number=db.Column(db.Integer,nullable=False,default=1); is_active=db.Column(db.Boolean,nullable=False,default=True); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    course=db.relationship('Course',back_populates='subjects'); classes=db.relationship('AcademicClass',back_populates='subject')

class AcademicClass(db.Model):
    __tablename__='classes'
    id=db.Column(db.Integer,primary_key=True); subject_id=db.Column(db.Integer,db.ForeignKey('subjects.id',ondelete='RESTRICT'),nullable=False,index=True); semester_id=db.Column(db.Integer,db.ForeignKey('semesters.id',ondelete='RESTRICT'),nullable=False,index=True); teacher_id=db.Column(db.Integer,db.ForeignKey('teachers.id',ondelete='RESTRICT'),index=True); code=db.Column(db.String(50),unique=True,nullable=False,index=True); room=db.Column(db.String(50)); weekday=db.Column(db.Integer); start_time=db.Column(db.Time); end_time=db.Column(db.Time); is_active=db.Column(db.Boolean,nullable=False,default=True,index=True); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow); updated_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow,onupdate=utcnow)
    subject=db.relationship('Subject',back_populates='classes'); semester=db.relationship('Semester',back_populates='classes'); teacher=db.relationship('Teacher',back_populates='classes'); enrollments=db.relationship('Enrollment',back_populates='academic_class',cascade='all, delete-orphan'); assessments=db.relationship('Assessment',back_populates='academic_class',cascade='all, delete-orphan')

class Enrollment(db.Model):
    __tablename__='enrollments'
    id=db.Column(db.Integer,primary_key=True); student_id=db.Column(db.Integer,db.ForeignKey('students.id',ondelete='CASCADE'),nullable=False,index=True); class_id=db.Column(db.Integer,db.ForeignKey('classes.id',ondelete='CASCADE'),nullable=False,index=True); status=db.Column(db.String(20),nullable=False,default='active',index=True); enrolled_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    __table_args__=(db.UniqueConstraint('student_id','class_id',name='uq_enrollment_student_class'), db.CheckConstraint("status IN ('active','dropped','completed')",name='ck_enrollment_status'))
    student=db.relationship('Student',back_populates='enrollments'); academic_class=db.relationship('AcademicClass',back_populates='enrollments'); grades=db.relationship('Grade',back_populates='enrollment',cascade='all, delete-orphan'); attendance=db.relationship('Attendance',back_populates='enrollment',cascade='all, delete-orphan')

class Assessment(db.Model):
    __tablename__='assessments'
    id=db.Column(db.Integer,primary_key=True); class_id=db.Column(db.Integer,db.ForeignKey('classes.id',ondelete='CASCADE'),nullable=False,index=True); title=db.Column(db.String(180),nullable=False); assessment_date=db.Column(db.Date,nullable=False); max_score=db.Column(db.Float,nullable=False,default=10.0); weight=db.Column(db.Float,nullable=False,default=1.0); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    academic_class=db.relationship('AcademicClass',back_populates='assessments'); grades=db.relationship('Grade',back_populates='assessment',cascade='all, delete-orphan')

class Grade(db.Model):
    __tablename__='grades'
    id=db.Column(db.Integer,primary_key=True); assessment_id=db.Column(db.Integer,db.ForeignKey('assessments.id',ondelete='CASCADE'),nullable=False,index=True); enrollment_id=db.Column(db.Integer,db.ForeignKey('enrollments.id',ondelete='CASCADE'),nullable=False,index=True); score=db.Column(db.Float,nullable=False); entered_by=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='RESTRICT'),nullable=False); entered_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow); updated_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow,onupdate=utcnow)
    __table_args__=(db.UniqueConstraint('assessment_id','enrollment_id',name='uq_grade_assessment_enrollment'),)
    assessment=db.relationship('Assessment',back_populates='grades'); enrollment=db.relationship('Enrollment',back_populates='grades'); entered_by_user=db.relationship('User',foreign_keys=[entered_by])

class Attendance(db.Model):
    __tablename__='attendance'
    id=db.Column(db.Integer,primary_key=True); enrollment_id=db.Column(db.Integer,db.ForeignKey('enrollments.id',ondelete='CASCADE'),nullable=False,index=True); attendance_date=db.Column(db.Date,nullable=False,index=True); status=db.Column(db.String(20),nullable=False); recorded_by=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='RESTRICT'),nullable=False); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow); updated_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow,onupdate=utcnow)
    __table_args__=(db.UniqueConstraint('enrollment_id','attendance_date',name='uq_attendance_enrollment_date'), db.CheckConstraint("status IN ('present','absent','justified')",name='ck_attendance_status'))
    enrollment=db.relationship('Enrollment',back_populates='attendance'); recorded_by_user=db.relationship('User',foreign_keys=[recorded_by])

class AcademicCalendar(db.Model):
    __tablename__='academic_calendar'
    id=db.Column(db.Integer,primary_key=True); semester_id=db.Column(db.Integer,db.ForeignKey('semesters.id',ondelete='CASCADE'),nullable=False,index=True); title=db.Column(db.String(180),nullable=False); description=db.Column(db.Text); event_date=db.Column(db.Date,nullable=False,index=True); event_type=db.Column(db.String(50),nullable=False,default='geral'); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow); updated_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow,onupdate=utcnow)
    semester=db.relationship('Semester',back_populates='events')

class Permission(db.Model):
    __tablename__='permissions'
    id=db.Column(db.Integer,primary_key=True); code=db.Column(db.String(80),unique=True,nullable=False,index=True); name=db.Column(db.String(160),nullable=False); description=db.Column(db.String(300))
    users=db.relationship('UserPermission',back_populates='permission',cascade='all, delete-orphan')

class UserPermission(db.Model):
    __tablename__='user_permissions'
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='CASCADE'),nullable=False,index=True); permission_id=db.Column(db.Integer,db.ForeignKey('permissions.id',ondelete='CASCADE'),nullable=False,index=True); assigned_by=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='RESTRICT')); assigned_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    __table_args__=(db.UniqueConstraint('user_id','permission_id',name='uq_user_permission'),)
    user=db.relationship('User',foreign_keys=[user_id],back_populates='permissions'); permission=db.relationship('Permission',back_populates='users'); assigned_by_user=db.relationship('User',foreign_keys=[assigned_by])

class AuditLog(db.Model):
    __tablename__='audit_logs'
    id=db.Column(db.Integer,primary_key=True); actor_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='SET NULL'),index=True); action=db.Column(db.String(120),nullable=False,index=True); entity_type=db.Column(db.String(80),index=True); entity_id=db.Column(db.Integer); details=db.Column(db.Text); ip_address=db.Column(db.String(64)); user_agent=db.Column(db.String(500)); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow,index=True)
    actor=db.relationship('User',foreign_keys=[actor_id])

class PasswordResetToken(db.Model):
    __tablename__='password_reset_tokens'
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='CASCADE'),nullable=False,index=True); token_hash=db.Column(db.String(64),unique=True,nullable=False,index=True); expires_at=db.Column(db.DateTime(timezone=True),nullable=False,index=True); used_at=db.Column(db.DateTime(timezone=True)); created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=utcnow)
    user=db.relationship('User')
