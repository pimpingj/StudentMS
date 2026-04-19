from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import (User, Class, Course, Teacher, Student,
                        Grade, Attendance, Prediction, Notification,
                        Exam, exam_classes)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_teachers=total_teachers)


# ── 用户列表 ──────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/user_list.html', users=users)


# ── 创建用户 ──────────────────────────────────────────
@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    classes = Class.query.all()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role     = request.form.get('role')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('admin/create_user.html', classes=classes)

        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == 'student':
            name          = request.form.get('name', '').strip() or username
            gender        = request.form.get('gender', 'Other')
            date_of_birth = request.form.get('date_of_birth') or None
            class_id      = request.form.get('class_id') or None
            db.session.add(Student(user_id=user.user_id, name=name,
                                   gender=gender, date_of_birth=date_of_birth,
                                   class_id=class_id))
        elif role == 'teacher':
            teacher_name = request.form.get('teacher_name', '').strip() or username
            department   = request.form.get('department', '').strip() or None
            db.session.add(Teacher(user_id=user.user_id, name=teacher_name,
                                   department=department))

        db.session.commit()
        flash(f'User "{username}" created successfully.', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/create_user.html', classes=classes)


# ── 编辑用户 ──────────────────────────────────────────
@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user    = User.query.get_or_404(user_id)
    classes = Class.query.all()

    if request.method == 'POST':
        new_username = request.form.get('username').strip()
        if new_username != user.username and User.query.filter_by(username=new_username).first():
            flash('Username already exists.', 'danger')
            return render_template('admin/edit_user.html', user=user, classes=classes)

        user.username = new_username
        new_password  = request.form.get('password', '').strip()
        if new_password:
            user.set_password(new_password)

        # 更新 student profile
        if user.role == 'student':
            p = user.student_profile
            if p:
                p.name          = request.form.get('name', '').strip() or user.username
                p.gender        = request.form.get('gender', 'Other')
                p.date_of_birth = request.form.get('date_of_birth') or None
                p.class_id      = request.form.get('class_id') or None

        # 更新 teacher profile
        elif user.role == 'teacher':
            p = user.teacher_profile
            if p:
                p.name       = request.form.get('teacher_name', '').strip() or user.username
                p.department = request.form.get('department', '').strip() or None

        db.session.commit()
        flash(f'User "{user.username}" updated.', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/edit_user.html', user=user, classes=classes)


# ── 删除用户 ──────────────────────────────────────────
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.user_id == current_user.user_id:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin.user_list'))

    # Delete in FK-safe order: children before parents.
    # Notifications reference users directly.
    Notification.query.filter_by(user_id=user.user_id).delete()

    if user.role == 'teacher' and user.teacher_profile:
        teacher = user.teacher_profile
        # Nullify FK on classes and courses (keep them, just unassign the teacher).
        Class.query.filter_by(teacher_id=teacher.teacher_id).update({'teacher_id': None})
        Course.query.filter_by(teacher_id=teacher.teacher_id).update({'teacher_id': None})
        # Exams require NOT NULL teacher_id — must be deleted along with their grades.
        for exam in teacher.exams.all():
            Grade.query.filter_by(exam_id=exam.exam_id).delete()
            db.session.execute(
                exam_classes.delete().where(exam_classes.c.exam_id == exam.exam_id)
            )
            db.session.delete(exam)
        db.session.flush()
        db.session.delete(teacher)
        db.session.flush()

    elif user.role == 'student' and user.student_profile:
        student = user.student_profile
        Prediction.query.filter_by(student_id=student.student_id).delete()
        Attendance.query.filter_by(student_id=student.student_id).delete()
        Grade.query.filter_by(student_id=student.student_id).delete()
        db.session.delete(student)
        db.session.flush()

    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', 'success')
    return redirect(url_for('admin.user_list'))


# ── 班级列表 ──────────────────────────────────────────
@admin_bp.route('/classes')
@login_required
@admin_required
def class_list():
    classes = Class.query.all()
    return render_template('admin/class_list.html', classes=classes)


# ── 创建班级 ──────────────────────────────────────────
@admin_bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_class():
    teachers = Teacher.query.all()
    if request.method == 'POST':
        class_name    = request.form.get('class_name')
        academic_year = request.form.get('academic_year')
        teacher_id    = request.form.get('teacher_id') or None
        db.session.add(Class(class_name=class_name, academic_year=academic_year,
                             teacher_id=teacher_id))
        db.session.commit()
        flash(f'Class "{class_name}" created.', 'success')
        return redirect(url_for('admin.class_list'))
    return render_template('admin/create_class.html', teachers=teachers)


# ── 编辑班级 ──────────────────────────────────────────
@admin_bp.route('/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_class(class_id):
    cls      = Class.query.get_or_404(class_id)
    teachers = Teacher.query.all()
    if request.method == 'POST':
        cls.class_name    = request.form.get('class_name')
        cls.academic_year = request.form.get('academic_year')
        cls.teacher_id    = request.form.get('teacher_id') or None
        db.session.commit()
        flash(f'Class "{cls.class_name}" updated.', 'success')
        return redirect(url_for('admin.class_list'))
    return render_template('admin/edit_class.html', cls=cls, teachers=teachers)


# ── 删除班级 ──────────────────────────────────────────
@admin_bp.route('/classes/delete/<int:class_id>', methods=['POST'])
@login_required
@admin_required
def delete_class(class_id):
    c = Class.query.get_or_404(class_id)
    db.session.delete(c)
    db.session.commit()
    flash(f'Class "{c.class_name}" deleted.', 'success')
    return redirect(url_for('admin.class_list'))


# ── 课程列表 ──────────────────────────────────────────
@admin_bp.route('/courses')
@login_required
@admin_required
def course_list():
    courses = Course.query.all()
    return render_template('admin/course_list.html', courses=courses)


# ── 创建课程 ──────────────────────────────────────────
@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_course():
    teachers = Teacher.query.all()
    classes  = Class.query.all()
    if request.method == 'POST':
        course_name = request.form.get('course_name')
        teacher_id  = request.form.get('teacher_id') or None
        class_id    = request.form.get('class_id') or None
        db.session.add(Course(course_name=course_name, teacher_id=teacher_id,
                              class_id=class_id))
        db.session.commit()
        flash(f'Course "{course_name}" created.', 'success')
        return redirect(url_for('admin.course_list'))
    return render_template('admin/create_course.html', teachers=teachers, classes=classes)


# ── 编辑课程 ──────────────────────────────────────────
@admin_bp.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course   = Course.query.get_or_404(course_id)
    teachers = Teacher.query.all()
    classes  = Class.query.all()
    if request.method == 'POST':
        course.course_name = request.form.get('course_name')
        course.teacher_id  = request.form.get('teacher_id') or None
        course.class_id    = request.form.get('class_id') or None
        db.session.commit()
        flash(f'Course "{course.course_name}" updated.', 'success')
        return redirect(url_for('admin.course_list'))
    return render_template('admin/edit_course.html', course=course,
                           teachers=teachers, classes=classes)


# ── 删除课程 ──────────────────────────────────────────
@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash(f'Course "{course.course_name}" deleted.', 'success')
    return redirect(url_for('admin.course_list'))
