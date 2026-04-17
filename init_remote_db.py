"""
One-time remote database initialisation script.
Run from project root: python init_remote_db.py

Connects using DATABASE_URL from config.py (remote database).
Safe to re-run — clears all non-essential data before re-seeding.
"""
from app import create_app, db
from app.models import (User, Class, Teacher, Student, Course,
                        Exam, Grade, Attendance, Notification,
                        Prediction, exam_classes)
from datetime import date, time, timedelta
import random

app = create_app()

with app.app_context():

    # ── 1. Create tables ───────────────────────────────────────────────────────
    print("Creating tables...")
    db.create_all()
    print("Tables ready.")

    # ── 2. Clear existing non-admin data (safe re-run) ────────────────────────
    print("Clearing old data...")
    Notification.query.delete()
    Prediction.query.delete()
    Attendance.query.delete()
    Grade.query.delete()
    db.session.execute(exam_classes.delete())
    Exam.query.delete()
    Course.query.delete()
    Student.query.delete()
    db.session.execute(Class.__table__.update().values(teacher_id=None))
    Teacher.query.delete()
    Class.query.delete()
    User.query.delete()
    db.session.commit()
    print("Cleared.")

    # ── 3. Admin account ───────────────────────────────────────────────────────
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()

    # ── 4. Teacher account ────────────────────────────────────────────────────
    teacher_user = User(username='teacher_a', role='teacher')
    teacher_user.set_password('teacher123')
    db.session.add(teacher_user)
    db.session.flush()

    teacher = Teacher(user_id=teacher_user.user_id,
                      name='Alice Smith', department='Science & Computing')
    db.session.add(teacher)
    db.session.flush()

    # ── 5. Class ──────────────────────────────────────────────────────────────
    cls_a = Class(class_name='Year 12 - Class A',
                  academic_year='2025-2026',
                  teacher_id=teacher.teacher_id)
    db.session.add(cls_a)
    db.session.flush()

    teacher.classes.append(cls_a)

    # ── 6. Student accounts ───────────────────────────────────────────────────
    def make_student(username, password, name, gender, dob, cls):
        u = User(username=username, role='student')
        u.set_password(password)
        db.session.add(u)
        db.session.flush()
        s = Student(user_id=u.user_id, name=name, gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    class_id=cls.class_id)
        db.session.add(s)
        db.session.flush()
        return s

    # Primary demo student
    stu_a = make_student('student_a', 'student123',
                         'Alex Johnson', 'Male', '2008-04-12', cls_a)

    # Two extra students so class stats / rankings are meaningful
    stu_b = make_student('student_b', 'student123',
                         'Beth Williams', 'Female', '2008-07-22', cls_a)
    stu_c = make_student('student_c', 'student123',
                         'Chris Lee', 'Male', '2008-11-05', cls_a)

    students = [stu_a, stu_b, stu_c]

    # ── 7. Courses ────────────────────────────────────────────────────────────
    maths = Course(course_name='Mathematics',
                   teacher_id=teacher.teacher_id, class_id=cls_a.class_id)
    cs    = Course(course_name='Computer Science',
                   teacher_id=teacher.teacher_id, class_id=cls_a.class_id)
    db.session.add_all([maths, cs])
    db.session.flush()

    # ── 8. Exams (3 past, 1 upcoming) ─────────────────────────────────────────
    today = date.today()
    exams = [
        Exam(name='Quiz 1',      exam_date=date(2025, 9, 20),
             teacher_id=teacher.teacher_id, classes=[cls_a]),
        Exam(name='Midterm',     exam_date=date(2026, 1, 15),
             teacher_id=teacher.teacher_id, classes=[cls_a]),
        Exam(name='Quiz 2',      exam_date=date(2026, 3, 10),
             teacher_id=teacher.teacher_id, classes=[cls_a]),
        Exam(name='Final Exam',  exam_date=date(2026, 6, 20),
             teacher_id=teacher.teacher_id, classes=[cls_a]),
    ]
    db.session.add_all(exams)
    db.session.flush()

    past_exams = [e for e in exams if e.exam_date < today]

    # ── 9. Grades (past exams only) ───────────────────────────────────────────
    random.seed(99)

    base_scores = {
        stu_a.student_id: 74,   # student_a: solid mid-range
        stu_b.student_id: 88,   # student_b: high performer
        stu_c.student_id: 61,   # student_c: struggling
    }

    for exam in past_exams:
        for course in [maths, cs]:
            for s in students:
                score = round(min(100, max(0,
                    base_scores[s.student_id] + random.gauss(0, 8))), 1)
                db.session.add(Grade(
                    student_id=s.student_id,
                    course_id=course.course_id,
                    exam_id=exam.exam_id,
                    score=score))

    # ── 10. Attendance (last 6 weeks, Mon/Wed/Fri) ────────────────────────────
    lesson_times = [time(9, 0), time(13, 0), time(15, 30)]

    att_profiles = {
        stu_a.student_id: 0.80,   # 80 % — healthy
        stu_b.student_id: 0.92,   # 92 %
        stu_c.student_id: 0.65,   # 65 % — below threshold (triggers alert)
    }

    for week in range(6):
        for day_i, day_offset in enumerate([0, 2, 4]):
            att_date = today - timedelta(weeks=week, days=day_offset)
            lt = lesson_times[day_i]
            for course in [maths, cs]:
                for s in students:
                    rate = att_profiles[s.student_id]
                    r = random.random()
                    if r < rate:
                        status = 'present'
                    elif r < rate + 0.06:
                        status = 'late'
                    else:
                        status = 'absent'
                    db.session.add(Attendance(
                        student_id=s.student_id,
                        course_id=course.course_id,
                        date=att_date,
                        lesson_time=lt,
                        status=status))

    db.session.commit()

    # ── 11. Demo notifications for student_a ──────────────────────────────────
    from app.models import Notification
    from datetime import datetime, timedelta as td

    now = datetime.utcnow()
    notifs = [
        Notification(user_id=stu_a.user_id, is_read=False,
                     created_at=now - td(days=2),
                     message="Your attendance rate has dropped to 68.3%, which is "
                             "below the 75% threshold. Please check your attendance record."),
        Notification(user_id=stu_a.user_id, is_read=False,
                     created_at=now - td(hours=5),
                     message="Your predicted grade for Mathematics is 57.2, which is "
                             "below 60. Consider seeking additional support."),
        Notification(user_id=stu_a.user_id, is_read=False,
                     created_at=now - td(minutes=20),
                     message="New exam 'Final Exam' has been scheduled on 2026-06-20 "
                             "for class Year 12 - Class A."),
    ]
    db.session.add_all(notifs)
    db.session.commit()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n=== Remote database initialised successfully ===")
    print()
    print("  ACCOUNTS")
    print("  ─────────────────────────────────────────")
    print("  Role     Username    Password")
    print("  Admin    admin       admin123")
    print("  Teacher  teacher_a   teacher123")
    print("  Student  student_a   student123")
    print("  Student  student_b   student123  (supporting data)")
    print("  Student  student_c   student123  (supporting data)")
    print()
    print("  SAMPLE DATA")
    print("  ─────────────────────────────────────────")
    print("  Class    : Year 12 - Class A (2025-2026)")
    print("  Courses  : Mathematics, Computer Science")
    print("  Exams    : Quiz 1, Midterm, Quiz 2 (past) | Final Exam (upcoming Jun 2026)")
    print("  Grades   : recorded for all 3 past exams × 2 courses × 3 students")
    print("  Attendance: 6 weeks of records")
    print("  Notifications: 3 unread for student_a")
