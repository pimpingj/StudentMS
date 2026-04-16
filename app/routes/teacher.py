import json
from collections import defaultdict
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import date, datetime as dt
from app import db
from app.models import Teacher, Course, Grade, Student, Attendance, Class, Exam, Prediction

teacher_bp = Blueprint('teacher', __name__)


def get_teacher_or_403():
    teacher = Teacher.query.filter_by(user_id=current_user.user_id).first()
    if not teacher:
        abort(403)
    return teacher


# ── Dashboard ─────────────────────────────────────────
@teacher_bp.route('/teacher/dashboard')
@login_required
def dashboard():
    teacher = Teacher.query.filter_by(user_id=current_user.user_id).first()
    at_risk_count = 0
    if teacher:
        course_ids = [c.course_id for c in teacher.courses]
        at_risk_count = (Prediction.query
                         .filter(Prediction.course_id.in_(course_ids),
                                 Prediction.model_type == 'linear_regression',
                                 Prediction.target == 'next_exam',
                                 Prediction.predicted_score < 65)
                         .count())
    return render_template('teacher/dashboard.html', at_risk_count=at_risk_count)


# ══════════════════════════════════════════════════════
#  考试管理
# ══════════════════════════════════════════════════════

@teacher_bp.route('/teacher/exams')
@login_required
def exam_list():
    teacher = get_teacher_or_403()
    exams   = teacher.exams.order_by(Exam.exam_date.desc()).all()
    return render_template('teacher/exam_list.html', exams=exams)


@teacher_bp.route('/teacher/exams/create', methods=['GET', 'POST'])
@login_required
def create_exam():
    teacher = get_teacher_or_403()
    classes = teacher.classes.all()

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        exam_date = request.form.get('exam_date') or str(date.today())
        class_ids = request.form.getlist('class_ids')

        # Only allow classes that belong to this teacher
        teacher_class_ids = {c.class_id for c in classes}
        selected_classes = [c for c in classes if str(c.class_id) in class_ids
                            and c.class_id in teacher_class_ids]
        exam = Exam(name=name, exam_date=exam_date,
                    teacher_id=teacher.teacher_id, classes=selected_classes)
        db.session.add(exam)
        db.session.commit()
        from app.notifications import notify_new_exam
        notify_new_exam(exam)
        db.session.commit()
        flash(f'Exam "{name}" created.', 'success')
        return redirect(url_for('teacher.exam_list'))

    return render_template('teacher/exam_form.html', classes=classes,
                           today=str(date.today()))


@teacher_bp.route('/teacher/exams/delete/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    teacher = get_teacher_or_403()
    exam    = Exam.query.get_or_404(exam_id)
    if exam.teacher_id != teacher.teacher_id:
        abort(403)
    db.session.delete(exam)
    db.session.commit()
    flash(f'Exam "{exam.name}" deleted.', 'success')
    return redirect(url_for('teacher.exam_list'))


# ══════════════════════════════════════════════════════
#  成绩管理
# ══════════════════════════════════════════════════════

@teacher_bp.route('/teacher/grades')
@login_required
def grade_list():
    teacher  = get_teacher_or_403()
    exam_ids = [e.exam_id for e in teacher.exams]
    grades   = (Grade.query
                .filter(Grade.exam_id.in_(exam_ids))
                .join(Exam).order_by(Exam.exam_date.desc())
                .all())
    return render_template('teacher/grade_list.html', grades=grades)


@teacher_bp.route('/teacher/grades/select', methods=['GET', 'POST'])
@login_required
def grade_select():
    """Step 1：选考试 + 课程"""
    teacher = get_teacher_or_403()
    exams   = teacher.exams.order_by(Exam.exam_date.desc()).all()
    courses = teacher.courses.all()

    if request.method == 'POST':
        exam_id   = request.form.get('exam_id')
        course_id = request.form.get('course_id')
        exam      = Exam.query.get_or_404(exam_id)
        if exam.teacher_id != teacher.teacher_id:
            abort(403)
        teacher_course_ids = {c.course_id for c in courses}
        if not course_id or int(course_id) not in teacher_course_ids:
            abort(403)
        class_ids = [c.class_id for c in exam.classes]
        return redirect(url_for('teacher.grade_bulk',
                                exam_id=exam_id, course_id=course_id,
                                class_ids=','.join(str(i) for i in class_ids)))

    return render_template('teacher/grade_select.html', exams=exams, courses=courses)


@teacher_bp.route('/teacher/grades/bulk', methods=['GET', 'POST'])
@login_required
def grade_bulk():
    """Step 2：为考试关联班级的全体学生录入分数"""
    teacher   = get_teacher_or_403()
    exam_id   = request.args.get('exam_id',   type=int)
    course_id = request.args.get('course_id', type=int)
    class_ids_str = request.args.get('class_ids', '')

    exam   = Exam.query.get_or_404(exam_id)
    course = Course.query.get_or_404(course_id)

    if exam.teacher_id != teacher.teacher_id:
        abort(403)
    course_ids = [c.course_id for c in teacher.courses]
    if course_id not in course_ids:
        abort(403)

    class_ids = [int(i) for i in class_ids_str.split(',') if i]
    students  = (Student.query
                 .filter(Student.class_id.in_(class_ids))
                 .order_by(Student.name).all()) if class_ids else Student.query.order_by(Student.name).all()

    if request.method == 'POST':
        for s in students:
            score_str = request.form.get(f'score_{s.student_id}', '').strip()
            if not score_str:
                continue
            existing = Grade.query.filter_by(
                student_id=s.student_id, course_id=course_id,
                exam_id=exam_id).first()
            if existing:
                existing.score = float(score_str)
            else:
                db.session.add(Grade(
                    student_id=s.student_id, course_id=course_id,
                    exam_id=exam_id, score=float(score_str)))
        db.session.commit()
        flash('Grades saved.', 'success')
        return redirect(url_for('teacher.grade_stats',
                                exam_id=exam_id, course_id=course_id))

    existing_grades = {
        g.student_id: g.score
        for g in Grade.query.filter_by(course_id=course_id, exam_id=exam_id).all()
    }
    return render_template('teacher/grade_bulk.html',
                           exam=exam, course=course, students=students,
                           existing_grades=existing_grades,
                           exam_id=exam_id, course_id=course_id,
                           class_ids=class_ids_str)


@teacher_bp.route('/teacher/grades/stats')
@login_required
def grade_stats():
    """Exam+course statistics shown automatically after grades are saved."""
    from app.stats import exam_course_stats
    teacher   = get_teacher_or_403()
    exam_id   = request.args.get('exam_id',   type=int)
    course_id = request.args.get('course_id', type=int)

    exam   = Exam.query.get_or_404(exam_id)
    course = Course.query.get_or_404(course_id)

    if exam.teacher_id != teacher.teacher_id:
        abort(403)
    if course_id not in [c.course_id for c in teacher.courses]:
        abort(403)

    stats = exam_course_stats(exam_id, course_id)
    return render_template('teacher/grade_stats.html',
                           exam=exam, course=course, stats=stats)


@teacher_bp.route('/teacher/stats')
@login_required
def stats_dashboard():
    """Overall statistics dashboard for the teacher."""
    from app.stats import course_overall_stats, class_attendance_rate
    teacher = get_teacher_or_403()
    courses = teacher.courses.all()
    classes = teacher.classes.all()

    course_summaries = [s for s in
                        (course_overall_stats(c) for c in courses)
                        if s is not None]

    class_summaries = [
        {
            'cls':      cls,
            'att_rate': class_attendance_rate(cls),
            'student_count': cls.students.count(),
        }
        for cls in classes
    ]

    course_ids = [c.course_id for c in courses]
    at_risk_count = (Prediction.query
                     .filter(Prediction.course_id.in_(course_ids),
                             Prediction.model_type == 'linear_regression',
                             Prediction.target == 'next_exam',
                             Prediction.predicted_score < 65)
                     .count())

    return render_template('teacher/stats_dashboard.html',
                           course_summaries=course_summaries,
                           class_summaries=class_summaries,
                           at_risk_count=at_risk_count)


@teacher_bp.route('/teacher/grades/delete/<int:grade_id>', methods=['POST'])
@login_required
def delete_grade(grade_id):
    teacher  = get_teacher_or_403()
    grade    = Grade.query.get_or_404(grade_id)
    exam_ids = [e.exam_id for e in teacher.exams]
    if grade.exam_id not in exam_ids:
        abort(403)
    db.session.delete(grade)
    db.session.commit()
    flash('Grade deleted.', 'success')
    return redirect(url_for('teacher.grade_list'))


# ══════════════════════════════════════════════════════
#  考勤管理
# ══════════════════════════════════════════════════════

@teacher_bp.route('/teacher/attendance')
@login_required
def attendance_list():
    teacher    = get_teacher_or_403()
    course_ids = [c.course_id for c in teacher.courses]
    records    = (Attendance.query
                  .filter(Attendance.course_id.in_(course_ids))
                  .order_by(Attendance.date.desc())
                  .all())
    return render_template('teacher/attendance_list.html', records=records)


@teacher_bp.route('/teacher/attendance/select', methods=['GET', 'POST'])
@login_required
def attendance_select():
    teacher = get_teacher_or_403()
    classes = teacher.classes.all()
    if request.method == 'POST':
        return redirect(url_for('teacher.attendance_bulk',
                                class_id=request.form.get('class_id')))
    return render_template('teacher/attendance_select.html', classes=classes)


@teacher_bp.route('/teacher/attendance/bulk', methods=['GET', 'POST'])
@login_required
def attendance_bulk():
    teacher  = get_teacher_or_403()
    class_id = request.args.get('class_id', type=int)
    cls      = Class.query.get_or_404(class_id)
    if cls.teacher_id != teacher.teacher_id:
        abort(403)
    courses  = teacher.courses.all()
    students = Student.query.filter_by(class_id=class_id).order_by(Student.name).all()

    if request.method == 'POST':
        course_id   = request.form.get('course_id')
        att_date    = request.form.get('att_date') or str(date.today())
        lesson_time = request.form.get('lesson_time') or None
        if lesson_time:
            lesson_time = dt.strptime(lesson_time, '%H:%M').time()

        if int(course_id) not in [c.course_id for c in courses]:
            abort(403)

        for s in students:
            status = request.form.get(f'status_{s.student_id}')
            if not status:
                continue
            existing = Attendance.query.filter_by(
                student_id=s.student_id, course_id=course_id,
                date=att_date, lesson_time=lesson_time).first()
            if existing:
                existing.status = status
            else:
                db.session.add(Attendance(
                    student_id=s.student_id, course_id=course_id,
                    date=att_date, lesson_time=lesson_time, status=status))
        db.session.commit()
        from app.notifications import check_attendance_alert
        for s in students:
            check_attendance_alert(s)
        db.session.commit()
        flash('Attendance saved.', 'success')
        return redirect(url_for('teacher.attendance_list'))

    return render_template('teacher/attendance_bulk.html',
                           cls=cls, courses=courses, students=students,
                           today=str(date.today()), class_id=class_id)


@teacher_bp.route('/teacher/attendance/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_attendance(record_id):
    teacher    = get_teacher_or_403()
    record     = Attendance.query.get_or_404(record_id)
    course_ids = [c.course_id for c in teacher.courses]
    if record.course_id not in course_ids:
        abort(403)
    courses  = teacher.courses.all()
    students = Student.query.filter_by(class_id=record.student.class_id).order_by(Student.name).all()

    if request.method == 'POST':
        record.course_id  = request.form.get('course_id')
        record.student_id = request.form.get('student_id')
        record.date       = request.form.get('att_date') or record.date
        lesson_time       = request.form.get('lesson_time') or None
        record.lesson_time = dt.strptime(lesson_time, '%H:%M').time() if lesson_time else None
        record.status     = request.form.get('status')
        db.session.commit()
        flash('Attendance updated.', 'success')
        return redirect(url_for('teacher.attendance_list'))

    return render_template('teacher/edit_attendance.html',
                           record=record, courses=courses, students=students)


@teacher_bp.route('/teacher/attendance/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_attendance(record_id):
    teacher    = get_teacher_or_403()
    record     = Attendance.query.get_or_404(record_id)
    course_ids = [c.course_id for c in teacher.courses]
    if record.course_id not in course_ids:
        abort(403)
    db.session.delete(record)
    db.session.commit()
    flash('Attendance deleted.', 'success')
    return redirect(url_for('teacher.attendance_list'))


# ══════════════════════════════════════════════════════
#  ML 预测
# ══════════════════════════════════════════════════════

@teacher_bp.route('/teacher/predictions', methods=['GET', 'POST'])
@login_required
def prediction_dashboard():
    from app.ml.predictor import train_and_evaluate, predict_students

    teacher   = get_teacher_or_403()
    courses   = teacher.courses.all()
    course_id = request.args.get('course_id', type=int)

    # 训练模型 + 取评估指标（每次请求都用模拟数据训练，速度很快）
    trained = train_and_evaluate()

    metrics = {
        target: {
            model: {k: v for k, v in info.items() if k != 'model'}
            for model, info in models.items()
        }
        for target, models in trained.items()
    }

    student_preds = []
    selected_course = None
    if course_id:
        teacher_course_ids = {c.course_id for c in courses}
        if course_id not in teacher_course_ids:
            abort(403)
        selected_course = Course.query.get(course_id)
        class_ids = list({c.class_id for c in courses if c.class_id})
        students  = Student.query.filter(Student.class_id.in_(class_ids)).all() if class_ids else Student.query.all()
        student_preds = predict_students(students, course_id, trained)

    # 保存预测结果到 DB
    if request.method == 'POST' and course_id and student_preds:
        Prediction.query.filter_by(course_id=course_id).delete()
        for row in student_preds:
            s = row['student']
            for target in ('next_exam', 'final_grade'):
                for model_name in ('linear_regression', 'decision_tree'):
                    db.session.add(Prediction(
                        student_id=s.student_id,
                        course_id=course_id,
                        model_type=model_name,
                        target=target,
                        predicted_score=row[target][model_name],
                        prediction_date=date.today(),
                    ))
        db.session.commit()
        from app.notifications import check_prediction_alert
        for row in student_preds:
            s = row['student']
            score = row['next_exam']['linear_regression']
            check_prediction_alert(s, selected_course.course_name, score)
        db.session.commit()
        flash('Predictions saved.', 'success')

    return render_template('teacher/prediction_dashboard.html',
                           courses=courses,
                           metrics=metrics,
                           student_preds=student_preds,
                           selected_course=selected_course,
                           course_id=course_id)


# ══════════════════════════════════════════════════════
#  Risk Alerts
# ══════════════════════════════════════════════════════

@teacher_bp.route('/teacher/risk-alerts')
@login_required
def risk_alerts():
    teacher    = get_teacher_or_403()
    course_ids = [c.course_id for c in teacher.courses]

    at_risk = (Prediction.query
               .filter(Prediction.course_id.in_(course_ids),
                       Prediction.model_type == 'linear_regression',
                       Prediction.target == 'next_exam',
                       Prediction.predicted_score < 65)
               .order_by(Prediction.predicted_score)
               .all())

    return render_template('teacher/risk_alerts.html', at_risk=at_risk)


# ══════════════════════════════════════════════════════
#  Teacher Charts
# ══════════════════════════════════════════════════════

@teacher_bp.route('/teacher/charts')
@login_required
def teacher_charts():
    teacher = get_teacher_or_403()
    courses = teacher.courses.all()

    course_labels  = []
    avg_grades     = []
    avg_attendance = []

    for c in courses:
        course_labels.append(c.course_name)

        grades = Grade.query.filter_by(course_id=c.course_id).all()
        avg_grades.append(
            round(sum(g.score for g in grades) / len(grades), 1) if grades else 0
        )

        records = Attendance.query.filter_by(course_id=c.course_id).all()
        if records:
            present = sum(1 for a in records if a.status in ('present', 'late'))
            avg_attendance.append(round(present / len(records) * 100, 1))
        else:
            avg_attendance.append(0)

    return render_template('teacher/charts.html',
                           course_labels=json.dumps(course_labels),
                           avg_grades=json.dumps(avg_grades),
                           avg_attendance=json.dumps(avg_attendance))
