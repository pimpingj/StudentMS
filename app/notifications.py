from app import db
from app.models import Notification, Attendance


def _notify(user_id, message):
    """Add a notification to the session only if no identical unread one exists."""
    exists = Notification.query.filter_by(
        user_id=user_id, message=message, is_read=False
    ).first()
    if not exists:
        db.session.add(Notification(user_id=user_id, message=message))


def check_attendance_alert(student):
    """Create a notification if the student's overall attendance rate is below 75%."""
    records = Attendance.query.filter_by(student_id=student.student_id).all()
    if not records:
        return
    total   = len(records)
    present = sum(1 for r in records if r.status in ('present', 'late'))
    rate    = round(present / total * 100, 1)
    if rate < 75:
        _notify(
            student.user_id,
            f"Your attendance rate has dropped to {rate}%, which is below the 75% threshold. "
            f"Please check your attendance record."
        )


def check_prediction_alert(student, course_name, predicted_score):
    """Create a notification if a predicted score falls below 65."""
    if predicted_score < 65:
        _notify(
            student.user_id,
            f"Your predicted grade for {course_name} is {predicted_score:.1f}, "
            f"which is below 60. Consider seeking additional support."
        )


def notify_new_exam(exam):
    """Notify every student enrolled in the exam's classes that a new exam is published."""
    for cls in exam.classes:
        for student in cls.students:
            _notify(
                student.user_id,
                f"New exam '{exam.name}' has been scheduled on {exam.exam_date} "
                f"for class {cls.class_name}."
            )
