"""
Seed demonstration notifications for stu_001.
Run from project root:  python seed_notifications.py

Requires seed_data.py to have been run first so that stu_001 exists.
"""
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Student, Notification

app = create_app()

with app.app_context():

    # ── Locate the demo student ────────────────────────────────────────────────
    user = User.query.filter_by(username='stu_001').first()
    if not user:
        print("ERROR: stu_001 not found. Run 'python seed_data.py' first, then re-run this script.")
        raise SystemExit(1)

    student = Student.query.filter_by(user_id=user.user_id).first()
    if not student:
        print("ERROR: Student profile for stu_001 not found.")
        raise SystemExit(1)

    # ── Clear any previous demo notifications for this user ───────────────────
    deleted = Notification.query.filter_by(user_id=user.user_id).delete()
    db.session.commit()
    if deleted:
        print(f"Cleared {deleted} existing notification(s) for stu_001.")

    # ── Insert 3 unread notifications ─────────────────────────────────────────
    now = datetime.utcnow()

    notifications = [
        Notification(
            user_id    = user.user_id,
            message    = (
                "Your attendance rate has dropped to 62.5%, which is below the 75% "
                "threshold. Please check your attendance record."
            ),
            is_read    = False,
            created_at = now - timedelta(days=2),
        ),
        Notification(
            user_id    = user.user_id,
            message    = (
                "Your predicted grade for Mathematics is 54.3, which is below 60. "
                "Consider seeking additional support."
            ),
            is_read    = False,
            created_at = now - timedelta(hours=6),
        ),
        Notification(
            user_id    = user.user_id,
            message    = (
                "New exam 'End of Term Test' has been scheduled on 2026-05-10 "
                "for class Class A."
            ),
            is_read    = False,
            created_at = now - timedelta(minutes=30),
        ),
    ]

    db.session.add_all(notifications)
    db.session.commit()

    print("\n=== Demo notifications created ===")
    print(f"Student : {student.name}")
    print(f"  Notification 1 (2 days ago)  : Low attendance warning (62.5%)")
    print(f"  Notification 2 (6 hours ago) : Predicted grade warning (Mathematics, 54.3)")
    print(f"  Notification 3 (30 min ago)  : New exam published (End of Term Test)")
    print()
    print("┌─────────────────────────────────────────┐")
    print("│  LOGIN CREDENTIALS                      │")
    print("│  Username : stu_001                     │")
    print("│  Password : 123456                      │")
    print("└─────────────────────────────────────────┘")
    print()
    print("All 3 notifications are unread — the bell badge will show '3'.")
