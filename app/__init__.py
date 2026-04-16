from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models import User, Student, Teacher, Class, Course, Exam, Grade, Attendance, Prediction, Notification

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated and current_user.role == 'student':
            notifs = (Notification.query
                      .filter_by(user_id=current_user.user_id, is_read=False)
                      .order_by(Notification.created_at.desc())
                      .limit(15)
                      .all())
            return {'student_notifications': notifs, 'unread_count': len(notifs)}
        return {'student_notifications': [], 'unread_count': 0}

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.teacher import teacher_bp
    from app.routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    return app