from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import date

from models import (db, Parent, Student, Attendance, ExamResult,
                    FeePayment, Certificate, Announcement, Exam)

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')


def parent_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'parent':
            flash('Parent access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def get_parent():
    return Parent.query.filter_by(user_id=current_user.id).first()


@parent_bp.route('/dashboard')
@login_required
@parent_required
def dashboard():
    parent = get_parent()
    if not parent:
        flash('Parent profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    children = parent.children.filter_by(status='active').all()
    children_data = []

    for child in children:
        attendance_pct = child.attendance_percentage()
        recent_results = ExamResult.query.filter_by(student_id=child.id).order_by(
            ExamResult.created_at.desc()).limit(3).all()
        pending_fees = FeePayment.query.filter_by(student_id=child.id, status='pending').count()
        fee_due = sum(p.balance for p in FeePayment.query.filter_by(
            student_id=child.id, status='pending').all())

        upcoming_exams = []
        if child.class_id:
            upcoming_exams = Exam.query.filter_by(class_id=child.class_id, status='scheduled').filter(
                Exam.date >= date.today()
            ).order_by(Exam.date).limit(3).all()

        children_data.append({
            'student': child,
            'attendance_pct': attendance_pct,
            'recent_results': recent_results,
            'pending_fees': pending_fees,
            'fee_due': fee_due,
            'upcoming_exams': upcoming_exams,
        })

    announcements = Announcement.query.filter(
        Announcement.target_audience.in_(['all', 'parents']),
        Announcement.is_published == True
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    return render_template('parent/dashboard.html',
                           parent=parent,
                           children_data=children_data,
                           announcements=announcements)


@parent_bp.route('/child/<int:student_id>')
@login_required
@parent_required
def child_detail(student_id):
    parent = get_parent()
    student = parent.children.filter_by(id=student_id).first_or_404()
    results = ExamResult.query.filter_by(student_id=student_id).order_by(
        ExamResult.created_at.desc()).all()
    attendance = Attendance.query.filter_by(student_id=student_id).order_by(
        Attendance.date.desc()).limit(30).all()
    payments = FeePayment.query.filter_by(student_id=student_id).order_by(
        FeePayment.created_at.desc()).all()
    certificates = Certificate.query.filter_by(student_id=student_id).all()
    return render_template('parent/child_detail.html',
                           parent=parent, student=student,
                           results=results, attendance=attendance,
                           payments=payments, certificates=certificates)


@parent_bp.route('/child/<int:student_id>/attendance')
@login_required
@parent_required
def child_attendance(student_id):
    parent = get_parent()
    student = parent.children.filter_by(id=student_id).first_or_404()
    records = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).all()
    return render_template('parent/child_attendance.html',
                           parent=parent, student=student, records=records)


@parent_bp.route('/child/<int:student_id>/grades')
@login_required
@parent_required
def child_grades(student_id):
    parent = get_parent()
    student = parent.children.filter_by(id=student_id).first_or_404()
    results = ExamResult.query.filter_by(student_id=student_id).order_by(
        ExamResult.created_at.desc()).all()
    return render_template('parent/child_grades.html',
                           parent=parent, student=student, results=results)


@parent_bp.route('/profile')
@login_required
@parent_required
def profile():
    parent = get_parent()
    return render_template('parent/profile.html', parent=parent)
