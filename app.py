import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required
from config import Config

from models import db, User, Student, Teacher, Parent, Employee


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.student import student_bp
    from routes.teacher import teacher_bp
    from routes.parent import parent_bp
    from routes.hr import hr_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(hr_bp)

    # Main routes
    from flask import Blueprint
    main_bp = Blueprint('main', __name__)

    @main_bp.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return render_template('landing.html')

    @main_bp.route('/dashboard')
    @login_required
    def dashboard():
        role = current_user.role
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
        elif role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif role == 'parent':
            return redirect(url_for('parent.dashboard'))
        elif role == 'hr':
            return redirect(url_for('hr.dashboard'))
        else:
            flash('Unknown role. Contact administrator.', 'danger')
            return redirect(url_for('auth.logout'))

    app.register_blueprint(main_bp)

    # Context processors
    @app.context_processor
    def inject_globals():
        from models import Announcement
        announcements_count = 0
        if current_user.is_authenticated:
            announcements_count = Announcement.query.filter_by(is_published=True).count()
        return {
            'school_name': app.config.get('SCHOOL_NAME', 'EduManage Pro'),
            'school_email': app.config.get('SCHOOL_EMAIL', ''),
            'academic_year': app.config.get('ACADEMIC_YEAR', '2024-2025'),
            'announcements_count': announcements_count,
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
