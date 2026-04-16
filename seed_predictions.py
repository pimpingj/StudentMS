"""
Run ML predictions for all courses and save to DB.
Run: python seed_predictions.py
"""
from app import create_app, db
from app.models import Teacher, Course, Student, Prediction
from app.ml.predictor import train_and_evaluate, predict_students
from datetime import date

app = create_app()

with app.app_context():
    trained = train_and_evaluate()

    Prediction.query.delete()
    db.session.commit()

    total = 0
    for course in Course.query.all():
        students = Student.query.all()
        preds    = predict_students(students, course.course_id, trained)

        for row in preds:
            s = row['student']
            for target in ('next_exam', 'final_grade'):
                for model_name in ('linear_regression', 'decision_tree'):
                    db.session.add(Prediction(
                        student_id      = s.student_id,
                        course_id       = course.course_id,
                        model_type      = model_name,
                        target          = target,
                        predicted_score = row[target][model_name],
                        prediction_date = date.today(),
                    ))
            total += 1

    db.session.commit()
    print(f"Saved predictions for {total} student-course pairs.")

    # 打印 at-risk 汇总
    at_risk = Prediction.query.filter(
        Prediction.model_type == 'linear_regression',
        Prediction.target     == 'next_exam',
        Prediction.predicted_score < 65
    ).all()
    print(f"\nAt-risk students ({len(at_risk)} records):")
    for p in at_risk:
        print(f"  {p.student.name:20s} | {p.course.course_name:15s} | {p.predicted_score:.1f}")
