import json
from collections import defaultdict
from functools import wraps
from datetime import date
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Student, Grade, Exam, Attendance, Notification, Course

student_bp = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_student_or_403():
    student = Student.query.filter_by(user_id=current_user.user_id).first()
    if not student:
        abort(403)
    return student


def _build_timetable_rows(student):
    """Return exam rows sorted by date asc for the student's class."""
    cls = student.class_group
    if not cls:
        return []
    today = date.today()
    rows = []
    for exam in sorted(cls.exams, key=lambda e: e.exam_date):
        courses = Course.query.filter_by(
            teacher_id=exam.teacher_id,
            class_id=student.class_id
        ).all()
        delta = (exam.exam_date - today).days
        if delta < 0:
            urgency = 'past'
        elif delta <= 3:
            urgency = 'danger'
        elif delta <= 7:
            urgency = 'warning'
        else:
            urgency = 'upcoming'
        rows.append({
            'exam':      exam,
            'courses':   courses,
            'days_until': delta,
            'urgency':   urgency,
        })
    return rows


@student_bp.route('/student/dashboard')
@login_required
@student_required
def dashboard():
    student = Student.query.filter_by(user_id=current_user.user_id).first()
    upcoming = []
    if student:
        upcoming = [r for r in _build_timetable_rows(student) if r['urgency'] != 'past'][:3]
    return render_template('student/dashboard.html', upcoming_exams=upcoming)


@student_bp.route('/student/timetable')
@login_required
@student_required
def timetable():
    student = get_student_or_403()
    rows    = _build_timetable_rows(student)
    return render_template('student/timetable.html', rows=rows)


# ── 查看自己成绩 ───────────────────────────────────────
@student_bp.route('/student/grades')
@login_required
@student_required
def grade_list():
    from app.stats import exam_course_stats
    student = get_student_or_403()
    grades  = (Grade.query
               .filter_by(student_id=student.student_id)
               .join(Exam)
               .order_by(Exam.exam_date.desc())
               .all())

    # Cache stats per (exam_id, course_id) to avoid redundant queries
    _cache = {}
    rows = []
    for g in grades:
        key = (g.exam_id, g.course_id)
        if key not in _cache:
            _cache[key] = exam_course_stats(g.exam_id, g.course_id)
        st = _cache[key]
        if st:
            rank = st['rank_map'].get(student.student_id)
            diff = round(g.score - st['avg'], 1)
            n    = st['n']
        else:
            rank = diff = n = None
        rows.append({'grade': g, 'rank': rank, 'diff': diff, 'class_avg': st['avg'] if st else None, 'n': n})

    return render_template('student/grade_list.html', rows=rows)


# ── 查看自己出勤 ───────────────────────────────────────
@student_bp.route('/student/attendance')
@login_required
@student_required
def attendance():
    student = get_student_or_403()
    records = (Attendance.query
               .filter_by(student_id=student.student_id)
               .order_by(Attendance.date.desc())
               .all())
    total   = len(records)
    present = sum(1 for r in records if r.status in ('present', 'late'))
    att_rate = round(present / total * 100, 1) if total else 0
    return render_template('student/attendance.html',
                           records=records, att_rate=att_rate,
                           total=total, present=present,
                           absent=sum(1 for r in records if r.status == 'absent'),
                           late=sum(1 for r in records if r.status == 'late'))


# ── 个人进度图表 ───────────────────────────────────────
@student_bp.route('/student/charts')
@login_required
@student_required
def student_charts():
    student = get_student_or_403()

    # 成绩趋势：按课程分组，按考试日期升序
    grades = (Grade.query
              .filter_by(student_id=student.student_id)
              .join(Exam)
              .order_by(Exam.exam_date)
              .all())

    course_trends = defaultdict(lambda: {'labels': [], 'scores': []})
    for g in grades:
        key = g.course.course_name
        course_trends[key]['labels'].append(f"{g.exam.name} ({g.exam.exam_date})")
        course_trends[key]['scores'].append(g.score)

    trends = [
        {'course': course, 'labels': data['labels'], 'scores': data['scores']}
        for course, data in course_trends.items()
    ]

    # 出勤率
    records = Attendance.query.filter_by(student_id=student.student_id).all()
    total   = len(records)
    if total:
        present  = sum(1 for a in records if a.status in ('present', 'late'))
        att_rate = round(present / total * 100, 1)
        absent   = sum(1 for a in records if a.status == 'absent')
        late     = sum(1 for a in records if a.status == 'late')
    else:
        att_rate = present = absent = late = 0

    return render_template('student/charts.html',
                           trends=json.dumps(trends),
                           att_rate=att_rate,
                           total=total,
                           present=present,
                           absent=absent,
                           late=late)


# ── Notifications ──────────────────────────────────────
@student_bp.route('/student/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
@student_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.user_id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    return ('', 204)


@student_bp.route('/student/notifications/mark-all-read', methods=['POST'])
@login_required
@student_required
def mark_all_notifications_read():
    Notification.query.filter_by(
        user_id=current_user.user_id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return redirect(request.referrer or url_for('student.dashboard'))
