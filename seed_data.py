"""
Test data seed script.
Run from project root: python seed_data.py
"""
from app import create_app, db
from app.models import (User, Class, Teacher, Student, Course,
                        Exam, Grade, Attendance, Prediction, exam_classes)
from datetime import date, time, timedelta
import random

app = create_app()

with app.app_context():
    print("Clearing old data...")

    # 删除顺序：先清子表，再清父表，先清关联表
    Prediction.query.delete()
    Attendance.query.delete()
    Grade.query.delete()
    db.session.execute(exam_classes.delete())   # 清 M2M 关联表
    Exam.query.delete()
    Course.query.delete()
    Student.query.delete()
    # 先把 classes.teacher_id 置空，解除对 teachers 的外键依赖
    db.session.execute(Class.__table__.update().values(teacher_id=None))
    Teacher.query.delete()
    Class.query.delete()
    User.query.filter(User.role != 'admin').delete()
    db.session.commit()
    print("Old data cleared.")

    # ── 1. 班级 ────────────────────────────────────────
    cls_a = Class(class_name='Class A', academic_year='2025')
    cls_b = Class(class_name='Class B', academic_year='2025')
    db.session.add_all([cls_a, cls_b])
    db.session.flush()

    # ── 2. 教师 ────────────────────────────────────────
    def make_teacher(username, name, department):
        u = User(username=username, role='teacher')
        u.set_password('123456')
        db.session.add(u)
        db.session.flush()
        t = Teacher(user_id=u.user_id, name=name, department=department)
        db.session.add(t)
        db.session.flush()
        return t

    teacher_a = make_teacher('teacher_a', 'Alice Smith', 'Science')
    teacher_b = make_teacher('teacher_b', 'Bob Johnson', 'Arts')

    cls_a.teacher_id = teacher_a.teacher_id
    cls_b.teacher_id = teacher_b.teacher_id
    db.session.flush()

    # ── 3. 学生 ────────────────────────────────────────
    student_rows = [
        ('stu_001', 'Luben William',  'Male',   '2003-05-12', cls_a),
        ('stu_002', 'Emma Brown',     'Female', '2003-08-23', cls_a),
        ('stu_003', 'James Wilson',   'Male',   '2004-01-07', cls_a),
        ('stu_004', 'Sophia Davis',   'Female', '2003-11-30', cls_b),
        ('stu_005', 'Oliver Taylor',  'Male',   '2004-03-15', cls_b),
        ('stu_006', 'Isabella Moore', 'Female', '2003-07-19', cls_b),
    ]

    students = []
    for username, name, gender, dob, cls in student_rows:
        u = User(username=username, role='student')
        u.set_password('123456')
        db.session.add(u)
        db.session.flush()
        s = Student(user_id=u.user_id, name=name, gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    class_id=cls.class_id)
        db.session.add(s)
        db.session.flush()
        students.append(s)

    students_a = [s for s in students if s.class_id == cls_a.class_id]
    students_b = [s for s in students if s.class_id == cls_b.class_id]

    # ── 4. 课程 ────────────────────────────────────────
    math    = Course(course_name='Mathematics', teacher_id=teacher_a.teacher_id, class_id=cls_a.class_id)
    science = Course(course_name='Science',     teacher_id=teacher_a.teacher_id, class_id=cls_a.class_id)
    english = Course(course_name='English',     teacher_id=teacher_b.teacher_id, class_id=cls_b.class_id)
    history = Course(course_name='History',     teacher_id=teacher_b.teacher_id, class_id=cls_b.class_id)
    db.session.add_all([math, science, english, history])
    db.session.flush()

    # ── 5. 考试 ────────────────────────────────────────
    exams_a = [
        Exam(name='Quiz 1',  exam_date=date(2025, 3, 10), teacher_id=teacher_a.teacher_id, classes=[cls_a]),
        Exam(name='Midterm', exam_date=date(2025, 4, 15), teacher_id=teacher_a.teacher_id, classes=[cls_a]),
        Exam(name='Quiz 2',  exam_date=date(2025, 5, 20), teacher_id=teacher_a.teacher_id, classes=[cls_a]),
        Exam(name='Final',   exam_date=date(2025, 6, 25), teacher_id=teacher_a.teacher_id, classes=[cls_a]),
    ]
    exams_b = [
        Exam(name='Quiz 1',  exam_date=date(2025, 3, 12), teacher_id=teacher_b.teacher_id, classes=[cls_b]),
        Exam(name='Midterm', exam_date=date(2025, 4, 18), teacher_id=teacher_b.teacher_id, classes=[cls_b]),
        Exam(name='Quiz 2',  exam_date=date(2025, 5, 22), teacher_id=teacher_b.teacher_id, classes=[cls_b]),
        Exam(name='Final',   exam_date=date(2025, 6, 27), teacher_id=teacher_b.teacher_id, classes=[cls_b]),
    ]
    db.session.add_all(exams_a + exams_b)
    db.session.flush()

    # ── 6. 成绩 ────────────────────────────────────────
    random.seed(42)

    def rand_score(base, noise=10):
        return round(min(100, max(0, base + random.gauss(0, noise))), 1)

    base_a = {students_a[0].student_id: 72,
              students_a[1].student_id: 85,
              students_a[2].student_id: 60}

    base_b = {students_b[0].student_id: 78,
              students_b[1].student_id: 65,
              students_b[2].student_id: 90}

    for exam in exams_a:
        for course in [math, science]:
            for s in students_a:
                db.session.add(Grade(student_id=s.student_id, course_id=course.course_id,
                                     exam_id=exam.exam_id, score=rand_score(base_a[s.student_id])))

    for exam in exams_b:
        for course in [english, history]:
            for s in students_b:
                db.session.add(Grade(student_id=s.student_id, course_id=course.course_id,
                                     exam_id=exam.exam_id, score=rand_score(base_b[s.student_id])))

    # ── 7. 出勤（过去 4 周，每周 Mon/Wed/Fri）─────────────
    today = date.today()
    lesson_times = [time(9, 0), time(14, 0), time(16, 0)]

    def rand_status():
        r = random.random()
        return 'present' if r < 0.80 else ('late' if r < 0.92 else 'absent')

    for week in range(4):
        for i, day_offset in enumerate([0, 2, 4]):
            att_date = today - timedelta(weeks=week, days=day_offset)
            lt = lesson_times[i]
            for course in [math, science]:
                for s in students_a:
                    db.session.add(Attendance(student_id=s.student_id, course_id=course.course_id,
                                              date=att_date, lesson_time=lt, status=rand_status()))
            for course in [english, history]:
                for s in students_b:
                    db.session.add(Attendance(student_id=s.student_id, course_id=course.course_id,
                                              date=att_date, lesson_time=lt, status=rand_status()))

    db.session.commit()

    print("\n=== Seed data inserted successfully ===")
    print("Classes  : Class A (teacher_a), Class B (teacher_b)")
    print("Teachers : teacher_a / teacher_b   password: 123456")
    print("Students : stu_001 ~ stu_006        password: 123456")
    print("Courses  : Mathematics, Science, English, History")
    print("Exams    : Quiz1, Midterm, Quiz2, Final (each class x2 teachers)")
