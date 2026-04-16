"""
Pure calculation helpers. No Flask request context required.
All functions take model IDs or ORM objects and return plain dicts.
"""
from app.models import Grade, Attendance


def exam_course_stats(exam_id, course_id):
    """
    Statistics for one (exam, course) slice.

    Returns a dict with keys:
        n, avg, high, low, fail_count, fail_pct,
        rank_map  {student_id: rank (1 = best)},
        rows      list[{grade, rank, diff_from_avg}] sorted best→worst
    Returns None if no grades exist.
    """
    grades = Grade.query.filter_by(exam_id=exam_id, course_id=course_id).all()
    if not grades:
        return None

    scores = [g.score for g in grades]
    n      = len(scores)
    avg    = round(sum(scores) / n, 1)
    high   = max(scores)
    low    = min(scores)
    fail_count = sum(1 for s in scores if s < 60)
    fail_pct   = round(fail_count / n * 100, 1)

    sorted_desc = sorted(grades, key=lambda g: g.score, reverse=True)
    rank_map    = {g.student_id: i + 1 for i, g in enumerate(sorted_desc)}

    rows = [
        {
            'grade':         g,
            'rank':          rank_map[g.student_id],
            'diff_from_avg': round(g.score - avg, 1),
        }
        for g in sorted_desc
    ]

    return {
        'n': n, 'avg': avg, 'high': high, 'low': low,
        'fail_count': fail_count, 'fail_pct': fail_pct,
        'rank_map': rank_map,
        'rows': rows,
    }


def course_overall_stats(course):
    """
    Aggregate statistics for a course across all exams.

    Returns a dict with keys:
        course, n, avg, high, low, fail_count, fail_pct,
        dist  {'A': n, 'B': n, 'C': n, 'D': n, 'F': n},
        att_rate  float (%)
    Returns None if no grades exist.
    """
    grades = Grade.query.filter_by(course_id=course.course_id).all()
    if not grades:
        return None

    scores = [g.score for g in grades]
    n      = len(scores)
    avg    = round(sum(scores) / n, 1)
    high   = max(scores)
    low    = min(scores)
    fail_count = sum(1 for s in scores if s < 60)
    fail_pct   = round(fail_count / n * 100, 1)

    dist = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for s in scores:
        if   s >= 90: dist['A'] += 1
        elif s >= 80: dist['B'] += 1
        elif s >= 70: dist['C'] += 1
        elif s >= 60: dist['D'] += 1
        else:         dist['F'] += 1

    att_records = Attendance.query.filter_by(course_id=course.course_id).all()
    att_rate = 0.0
    if att_records:
        present  = sum(1 for a in att_records if a.status in ('present', 'late'))
        att_rate = round(present / len(att_records) * 100, 1)

    return {
        'course': course, 'n': n, 'avg': avg, 'high': high, 'low': low,
        'fail_count': fail_count, 'fail_pct': fail_pct,
        'dist': dist, 'att_rate': att_rate,
    }


def class_attendance_rate(cls):
    """
    Overall attendance rate (%) for all courses belonging to a class.
    Returns float, or 0.0 if no records.
    """
    course_ids = [c.course_id for c in cls.courses]
    if not course_ids:
        return 0.0
    records = Attendance.query.filter(Attendance.course_id.in_(course_ids)).all()
    if not records:
        return 0.0
    present = sum(1 for a in records if a.status in ('present', 'late'))
    return round(present / len(records) * 100, 1)
