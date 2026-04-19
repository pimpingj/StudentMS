"""
Remote database initialisation script — full dataset.
Run from project root: python init_remote_db.py
Safe to re-run (clears and re-seeds every time).
"""
from app import create_app, db
from app.models import (User, Class, Teacher, Student, Course,
                        Exam, Grade, Attendance, Notification,
                        Prediction, exam_classes)
from datetime import date, time, timedelta, datetime
import random

random.seed(42)
app = create_app()

with app.app_context():

    # ── 1. Create tables ───────────────────────────────────────────────────────
    print("Creating tables...")
    db.create_all()

    # ── 2. Clear all existing data ────────────────────────────────────────────
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

    # ── 3. Admin ───────────────────────────────────────────────────────────────
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()

    # ── 4. Teachers ───────────────────────────────────────────────────────────
    teacher_rows = [
        ('teacher_a', 'teacher123', 'Alice Smith',   'Mathematics & Science'),
        ('teacher_b', 'teacher123', 'Bob Johnson',   'Humanities'),
        ('teacher_c', 'teacher123', 'Carol White',   'Computing & IT'),
        ('teacher_d', 'teacher123', 'David Brown',   'Science'),
        ('teacher_e', 'teacher123', 'Emma Davis',    'Life Sciences'),
    ]

    teachers = []
    for uname, pwd, name, dept in teacher_rows:
        u = User(username=uname, role='teacher')
        u.set_password(pwd)
        db.session.add(u)
        db.session.flush()
        t = Teacher(user_id=u.user_id, name=name, department=dept)
        db.session.add(t)
        db.session.flush()
        teachers.append(t)

    ta, tb, tc, td, te = teachers

    # ── 5. Classes ────────────────────────────────────────────────────────────
    cls_10a = Class(class_name='Year 10 - Class A', academic_year='2025-2026', teacher_id=ta.teacher_id)
    cls_10b = Class(class_name='Year 10 - Class B', academic_year='2025-2026', teacher_id=tb.teacher_id)
    cls_11a = Class(class_name='Year 11 - Class A', academic_year='2025-2026', teacher_id=tc.teacher_id)
    cls_11b = Class(class_name='Year 11 - Class B', academic_year='2025-2026', teacher_id=td.teacher_id)
    cls_12a = Class(class_name='Year 12 - Class A', academic_year='2025-2026', teacher_id=te.teacher_id)
    classes = [cls_10a, cls_10b, cls_11a, cls_11b, cls_12a]
    db.session.add_all(classes)
    db.session.flush()

    # ── 6. Students (16 total across 5 classes) ───────────────────────────────
    student_rows = [
        # Year 10A
        ('student_01', 'Liam Turner',     'Male',   '2010-03-14', cls_10a),
        ('student_02', 'Sophia Clark',    'Female', '2010-07-22', cls_10a),
        ('student_03', 'Noah Evans',      'Male',   '2010-11-05', cls_10a),
        ('student_04', 'Mia Robinson',    'Female', '2010-01-30', cls_10a),
        # Year 10B
        ('student_05', 'James Wright',    'Male',   '2010-05-18', cls_10b),
        ('student_06', 'Emily Scott',     'Female', '2010-09-02', cls_10b),
        ('student_07', 'Benjamin Harris', 'Male',   '2010-12-20', cls_10b),
        # Year 11A
        ('student_08', 'Oliver Thomas',   'Male',   '2009-02-08', cls_11a),
        ('student_09', 'Charlotte Walker','Female', '2009-06-15', cls_11a),
        ('student_10', 'Elijah Hall',     'Male',   '2009-10-27', cls_11a),
        # Year 11B
        ('student_11', 'Lucas Young',     'Male',   '2009-04-03', cls_11b),
        ('student_12', 'Isabella King',   'Female', '2009-08-19', cls_11b),
        ('student_13', 'Mason Green',     'Male',   '2009-12-11', cls_11b),
        # Year 12A  (original demo students kept here)
        ('student_a',  'Alex Johnson',    'Male',   '2008-04-12', cls_12a),
        ('student_b',  'Beth Williams',   'Female', '2008-07-22', cls_12a),
        ('student_c',  'Chris Lee',       'Male',   '2008-11-05', cls_12a),
    ]

    all_students = []
    for uname, name, gender, dob, cls in student_rows:
        u = User(username=uname, role='student')
        u.set_password('student123')
        db.session.add(u)
        db.session.flush()
        s = Student(user_id=u.user_id, name=name, gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    class_id=cls.class_id)
        db.session.add(s)
        db.session.flush()
        all_students.append(s)

    def students_in(cls):
        return [s for s in all_students if s.class_id == cls.class_id]

    # ── 7. Courses ────────────────────────────────────────────────────────────
    course_rows = [
        ('Mathematics',        ta.teacher_id, cls_10a.class_id),
        ('Physics',            ta.teacher_id, cls_10a.class_id),
        ('English Literature', tb.teacher_id, cls_10b.class_id),
        ('History',            tb.teacher_id, cls_10b.class_id),
        ('Computer Science',   tc.teacher_id, cls_11a.class_id),
        ('Information Technology', tc.teacher_id, cls_11a.class_id),
        ('Chemistry',          td.teacher_id, cls_11b.class_id),
        ('Biology',            td.teacher_id, cls_11b.class_id),
        ('Mathematics Advanced', te.teacher_id, cls_12a.class_id),
        ('Geography',          te.teacher_id, cls_12a.class_id),
    ]

    courses = []
    for cname, tid, cid in course_rows:
        c = Course(course_name=cname, teacher_id=tid, class_id=cid)
        db.session.add(c)
        db.session.flush()
        courses.append(c)

    def courses_for(cls):
        return [c for c in courses if c.class_id == cls.class_id]

    # ── 8. Exams (4 per class: 3 past + 1 upcoming) ───────────────────────────
    today = date.today()

    exam_schedule = {
        cls_10a: [
            ('Quiz 1',    date(2025, 9, 15), ta),
            ('Midterm',   date(2026, 1, 20), ta),
            ('Quiz 2',    date(2026, 3, 18), ta),
            ('Final Exam',date(2026, 6, 22), ta),
        ],
        cls_10b: [
            ('Quiz 1',    date(2025, 9, 17), tb),
            ('Midterm',   date(2026, 1, 22), tb),
            ('Quiz 2',    date(2026, 3, 20), tb),
            ('Final Exam',date(2026, 6, 24), tb),
        ],
        cls_11a: [
            ('Quiz 1',    date(2025, 9, 19), tc),
            ('Midterm',   date(2026, 1, 24), tc),
            ('Quiz 2',    date(2026, 3, 22), tc),
            ('Final Exam',date(2026, 6, 26), tc),
        ],
        cls_11b: [
            ('Quiz 1',    date(2025, 9, 21), td),
            ('Midterm',   date(2026, 1, 26), td),
            ('Quiz 2',    date(2026, 3, 24), td),
            ('Final Exam',date(2026, 6, 28), td),
        ],
        cls_12a: [
            ('Quiz 1',    date(2025, 9, 23), te),
            ('Midterm',   date(2026, 1, 28), te),
            ('Quiz 2',    date(2026, 3, 26), te),
            ('Final Exam',date(2026, 6, 30), te),
        ],
    }

    all_exams_by_class = {}
    for cls, schedule in exam_schedule.items():
        exams_for_cls = []
        for ename, edate, teacher in schedule:
            e = Exam(name=ename, exam_date=edate,
                     teacher_id=teacher.teacher_id, classes=[cls])
            db.session.add(e)
            db.session.flush()
            exams_for_cls.append(e)
        all_exams_by_class[cls.class_id] = exams_for_cls

    # ── 9. Grades ─────────────────────────────────────────────────────────────
    # Each student has a base score; noise added per exam to simulate variation.
    base_scores = {
        # Year 10A
        'student_01': 82,   # solid
        'student_02': 91,   # high achiever
        'student_03': 67,   # average
        'student_04': 55,   # struggling
        # Year 10B
        'student_05': 78,
        'student_06': 88,
        'student_07': 62,
        # Year 11A
        'student_08': 74,
        'student_09': 93,
        'student_10': 58,
        # Year 11B
        'student_11': 70,
        'student_12': 85,
        'student_13': 61,
        # Year 12A
        'student_a':  74,
        'student_b':  88,
        'student_c':  61,
    }

    username_map = {u.username: u for u in User.query.all()}
    student_username_map = {}
    for s in all_students:
        uname = User.query.get(s.user_id).username
        student_username_map[uname] = s

    for cls in classes:
        cls_students  = students_in(cls)
        cls_courses   = courses_for(cls)
        cls_exams     = all_exams_by_class[cls.class_id]
        past_exams    = [e for e in cls_exams if e.exam_date < today]

        for exam in past_exams:
            for course in cls_courses:
                for s in cls_students:
                    uname = User.query.get(s.user_id).username
                    base  = base_scores.get(uname, 70)
                    score = round(min(100, max(0, base + random.gauss(0, 9))), 1)
                    db.session.add(Grade(
                        student_id=s.student_id,
                        course_id=course.course_id,
                        exam_id=exam.exam_id,
                        score=score))

    db.session.commit()
    print("Grades inserted.")

    # ── 10. Attendance (8 weeks, Mon/Wed/Fri) ──────────────────────────────────
    lesson_times = [time(9, 0), time(13, 0), time(15, 30)]

    # Per-student attendance probability (present+late rate)
    att_rates = {
        'student_01': 0.88,
        'student_02': 0.95,
        'student_03': 0.72,   # borderline
        'student_04': 0.62,   # below 75% — triggers alert
        'student_05': 0.90,
        'student_06': 0.85,
        'student_07': 0.68,   # below 75%
        'student_08': 0.91,
        'student_09': 0.97,
        'student_10': 0.60,   # below 75%
        'student_11': 0.80,
        'student_12': 0.93,
        'student_13': 0.75,
        'student_a':  0.80,
        'student_b':  0.92,
        'student_c':  0.65,   # below 75%
    }

    for cls in classes:
        cls_students = students_in(cls)
        cls_courses  = courses_for(cls)

        for week in range(8):
            for day_i, day_offset in enumerate([0, 2, 4]):
                att_date = today - timedelta(weeks=week, days=day_offset)
                lt = lesson_times[day_i]
                for course in cls_courses:
                    for s in cls_students:
                        uname = User.query.get(s.user_id).username
                        rate  = att_rates.get(uname, 0.82)
                        r = random.random()
                        if r < rate * 0.88:
                            status = 'present'
                        elif r < rate:
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
    print("Attendance inserted.")

    # ── 11. Notifications for student_a ───────────────────────────────────────
    stu_a_user = User.query.filter_by(username='student_a').first()
    now = datetime.utcnow()
    notifs = [
        Notification(user_id=stu_a_user.user_id, is_read=False,
                     created_at=now - timedelta(days=2),
                     message="Your attendance rate has dropped to 68.3%, which is "
                             "below the 75% threshold. Please check your attendance record."),
        Notification(user_id=stu_a_user.user_id, is_read=False,
                     created_at=now - timedelta(hours=5),
                     message="Your predicted grade for Mathematics Advanced is 57.2, "
                             "which is below 60. Consider seeking additional support."),
        Notification(user_id=stu_a_user.user_id, is_read=False,
                     created_at=now - timedelta(minutes=20),
                     message="New exam 'Final Exam' has been scheduled on 2026-06-30 "
                             "for class Year 12 - Class A."),
    ]
    db.session.add_all(notifs)
    db.session.commit()

    # ── Summary ───────────────────────────────────────────────────────────────
    grade_count = Grade.query.count()
    att_count   = Attendance.query.count()

    print("\n=== Database seeded successfully ===")
    print()
    print("ACCOUNTS")
    print(f"  admin      / admin123    (Admin)")
    print(f"  teacher_a~e / teacher123 (5 Teachers)")
    print(f"  student_a~c / student123 (Year 12A demo students)")
    print(f"  student_01~13 / student123 (13 more students)")
    print()
    print("CLASSES & TEACHERS")
    for cls in classes:
        t = Teacher.query.get(cls.teacher_id)
        print(f"  {cls.class_name:30s} → {t.name}")
    print()
    print("COURSES:", len(courses))
    print("EXAMS:  ", sum(len(v) for v in all_exams_by_class.values()))
    print("GRADES: ", grade_count)
    print("ATTEND: ", att_count)
