"""
ML predictor module
Features : avg_score, attendance_rate (%), assignment_rate (%), last_exam_score
Targets  : next_exam_score, final_grade
Models   : Linear Regression, Decision Tree
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ── 模拟数据生成 ──────────────────────────────────────
def generate_synthetic_data(n=400, seed=42):
    np.random.seed(seed)

    avg_score       = np.random.normal(65, 15, n).clip(0, 100)
    attendance_rate = np.random.beta(8, 2, n) * 100          # 0–100
    assignment_rate = np.random.beta(7, 2, n) * 100          # 0–100
    last_exam_score = (avg_score + np.random.normal(0, 10, n)).clip(0, 100)

    noise_next  = np.random.normal(0, 5, n)
    noise_final = np.random.normal(0, 3, n)

    next_exam_score = (
        0.40 * avg_score +
        0.25 * last_exam_score +
        0.20 * attendance_rate +
        0.15 * assignment_rate +
        noise_next
    ).clip(0, 100)

    final_grade = (
        0.50 * avg_score +
        0.20 * attendance_rate +
        0.20 * assignment_rate +
        0.10 * last_exam_score +
        noise_final
    ).clip(0, 100)

    X = np.column_stack([avg_score, attendance_rate, assignment_rate, last_exam_score])
    return X, next_exam_score, final_grade


# ── 训练 & 评估 ───────────────────────────────────────
def train_and_evaluate():
    X, y_next, y_final = generate_synthetic_data()

    results = {}

    for target_name, y in [('next_exam', y_next), ('final_grade', y_final)]:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        models = {
            'linear_regression': LinearRegression(),
            'decision_tree':     DecisionTreeRegressor(max_depth=5, random_state=42),
        }

        target_results = {}
        for model_name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            target_results[model_name] = {
                'model': model,
                'mae':   round(mean_absolute_error(y_test, y_pred), 3),
                'rmse':  round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 3),
                'r2':    round(r2_score(y_test, y_pred), 4),
            }

        results[target_name] = target_results

    return results


# ── 从真实学生数据提取特征 ──────────────────────────────
def extract_student_features(student, course_id):
    """
    Returns [avg_score, attendance_rate, assignment_rate, last_exam_score]
    or None if insufficient data.
    assignment_rate is approximated from avg_score when no dedicated data exists.
    """
    from app.models import Grade, Attendance, Exam

    grades = (Grade.query
              .filter_by(student_id=student.student_id, course_id=course_id)
              .join(Exam).order_by(Exam.exam_date)
              .all())

    if not grades:
        return None

    scores          = [g.score for g in grades]
    avg_score       = float(np.mean(scores))
    last_exam_score = float(scores[-1])

    att_records = Attendance.query.filter_by(
        student_id=student.student_id, course_id=course_id).all()
    if att_records:
        present = sum(1 for a in att_records if a.status in ('present', 'late'))
        attendance_rate = present / len(att_records) * 100
    else:
        attendance_rate = 75.0   # fallback

    # assignment_rate: 无专项数据时用成绩均值近似
    assignment_rate = avg_score

    return [avg_score, attendance_rate, assignment_rate, last_exam_score]


# ── 对真实学生批量预测 ────────────────────────────────
def predict_students(students, course_id, trained_results):
    """
    Returns list of dicts:
    { student, features, next_exam: {lr, dt}, final_grade: {lr, dt} }
    """
    predictions = []

    for s in students:
        feat = extract_student_features(s, course_id)
        if feat is None:
            continue

        X = np.array([feat])
        row = {'student': s, 'features': feat}

        for target in ('next_exam', 'final_grade'):
            row[target] = {}
            for model_name in ('linear_regression', 'decision_tree'):
                model = trained_results[target][model_name]['model']
                score = float(np.clip(model.predict(X)[0], 0, 100))
                row[target][model_name] = round(score, 1)

        predictions.append(row)

    return predictions
