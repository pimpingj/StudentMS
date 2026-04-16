from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


# ── 1. users ──────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.Enum('admin', 'teacher', 'student'), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship('Student', backref='user', uselist=False)
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ── 2. classes ────────────────────────────────────────
class Class(db.Model):
    __tablename__ = 'classes'

    class_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name    = db.Column(db.String(100), nullable=False)
    teacher_id    = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=True)
    academic_year = db.Column(db.String(20), nullable=True)

    students = db.relationship('Student', backref='class_group', lazy='dynamic')
    courses  = db.relationship('Course',  backref='class_group', lazy='dynamic')


# ── 3. teachers ───────────────────────────────────────
class Teacher(db.Model):
    __tablename__ = 'teachers'

    teacher_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=True)

    classes = db.relationship('Class',  backref='teacher', lazy='dynamic')
    courses = db.relationship('Course', backref='teacher', lazy='dynamic')
    exams   = db.relationship('Exam',   backref='teacher', lazy='dynamic')


# ── 4. students ───────────────────────────────────────
class Student(db.Model):
    __tablename__ = 'students'

    student_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name          = db.Column(db.String(100), nullable=False)
    gender        = db.Column(db.Enum('Male', 'Female', 'Other'), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    class_id      = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=True)

    grades             = db.relationship('Grade',      backref='student', lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic')
    predictions        = db.relationship('Prediction', backref='student', lazy='dynamic')


# ── 5. courses ────────────────────────────────────────
class Course(db.Model):
    __tablename__ = 'courses'

    course_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_name = db.Column(db.String(100), nullable=False)
    teacher_id  = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=True)
    class_id    = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=True)

    grades             = db.relationship('Grade',      backref='course', lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='course', lazy='dynamic')
    predictions        = db.relationship('Prediction', backref='course', lazy='dynamic')


# ── 6. exam_classes 关联表 ────────────────────────────
exam_classes = db.Table(
    'exam_classes',
    db.Column('exam_id',  db.Integer, db.ForeignKey('exams.exam_id'),    primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('classes.class_id'), primary_key=True),
)


# ── 7. exams ──────────────────────────────────────────
class Exam(db.Model):
    __tablename__ = 'exams'

    exam_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name       = db.Column(db.String(100), nullable=False)
    exam_date  = db.Column(db.Date, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)

    classes = db.relationship('Class', secondary=exam_classes, backref='exams')
    grades  = db.relationship('Grade', backref='exam', lazy='dynamic')


# ── 8. grades ─────────────────────────────────────────
class Grade(db.Model):
    __tablename__ = 'grades'

    grade_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    course_id  = db.Column(db.Integer, db.ForeignKey('courses.course_id'),   nullable=False)
    exam_id    = db.Column(db.Integer, db.ForeignKey('exams.exam_id'),        nullable=False)
    score      = db.Column(db.Float, nullable=False)


# ── 9. attendance ─────────────────────────────────────
class Attendance(db.Model):
    __tablename__ = 'attendance'

    attendance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    course_id     = db.Column(db.Integer, db.ForeignKey('courses.course_id'),   nullable=False)
    date          = db.Column(db.Date, default=date.today, nullable=False)
    lesson_time   = db.Column(db.Time, nullable=True)
    status        = db.Column(db.Enum('present', 'absent', 'late'), nullable=False)


# ── 11. notifications ─────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    message    = db.Column(db.String(500), nullable=False)
    is_read    = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── 10. predictions ───────────────────────────────────
class Prediction(db.Model):
    __tablename__ = 'predictions'

    prediction_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id      = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    course_id       = db.Column(db.Integer, db.ForeignKey('courses.course_id'),   nullable=False)
    model_type      = db.Column(db.Enum('linear_regression', 'decision_tree'),    nullable=False)
    target          = db.Column(db.Enum('next_exam', 'final_grade'),              nullable=False)
    predicted_score = db.Column(db.Float, nullable=False)
    prediction_date = db.Column(db.Date, default=date.today)
