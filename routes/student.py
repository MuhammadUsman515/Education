from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import date

from models import (db, Student, Subject, Attendance, Exam, ExamResult,
                    Certificate, FeePayment, Announcement, Timetable)

student_bp = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Student access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def get_student():
    return Student.query.filter_by(user_id=current_user.id).first()


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = get_student()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    recent_results = ExamResult.query.filter_by(student_id=student.id).order_by(
        ExamResult.created_at.desc()).limit(5).all()

    attendance_pct = student.attendance_percentage()

    upcoming_exams = []
    if student.class_id:
        upcoming_exams = Exam.query.filter_by(class_id=student.class_id, status='scheduled').filter(
            Exam.date >= date.today()
        ).order_by(Exam.date).limit(5).all()

    fee_dues = FeePayment.query.filter_by(student_id=student.id, status='pending').all()
    total_due = sum(p.balance for p in fee_dues)

    announcements = Announcement.query.filter(
        Announcement.target_audience.in_(['all', 'students']),
        Announcement.is_published == True
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    return render_template('student/dashboard.html',
                           student=student,
                           recent_results=recent_results,
                           attendance_pct=attendance_pct,
                           upcoming_exams=upcoming_exams,
                           fee_dues=fee_dues,
                           total_due=total_due,
                           announcements=announcements)


@student_bp.route('/courses')
@login_required
@student_required
def courses():
    student = get_student()
    subjects = []
    if student and student.class_id:
        subjects = Subject.query.filter_by(class_id=student.class_id).all()
    return render_template('student/courses.html', student=student, subjects=subjects)


@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    student = get_student()
    records = Attendance.query.filter_by(student_id=student.id).order_by(
        Attendance.date.desc()).all()

    # Group by subject
    subject_attendance = {}
    for record in records:
        subject_name = record.subject.name if record.subject else 'General'
        if subject_name not in subject_attendance:
            subject_attendance[subject_name] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
        subject_attendance[subject_name]['total'] += 1
        if record.status in ['present', 'late']:
            subject_attendance[subject_name]['present'] += 1
        if record.status == 'absent':
            subject_attendance[subject_name]['absent'] += 1
        if record.status == 'late':
            subject_attendance[subject_name]['late'] += 1

    for name, data in subject_attendance.items():
        data['percentage'] = round((data['present'] / data['total']) * 100, 1) if data['total'] > 0 else 0

    return render_template('student/attendance.html',
                           student=student, records=records,
                           subject_attendance=subject_attendance,
                           attendance_pct=student.attendance_percentage())


@student_bp.route('/grades')
@login_required
@student_required
def grades():
    student = get_student()
    results = ExamResult.query.filter_by(student_id=student.id).order_by(
        ExamResult.created_at.desc()).all()

    # Group by exam type
    by_type = {}
    total_gpa = 0
    gpa_count = 0
    for r in results:
        etype = r.exam.exam_type if r.exam else 'other'
        if etype not in by_type:
            by_type[etype] = []
        by_type[etype].append(r)
        if r.grade_points:
            total_gpa += r.grade_points
            gpa_count += 1

    cgpa = round(total_gpa / gpa_count, 2) if gpa_count > 0 else 0

    return render_template('student/grades.html',
                           student=student, results=results,
                           by_type=by_type, cgpa=cgpa)


@student_bp.route('/fees')
@login_required
@student_required
def fees():
    student = get_student()
    payments = FeePayment.query.filter_by(student_id=student.id).order_by(
        FeePayment.created_at.desc()).all()
    total_paid = sum(p.amount_paid for p in payments if p.status in ['paid', 'partial'])
    total_due = sum(p.balance for p in payments if p.balance > 0)
    return render_template('student/fees.html', student=student,
                           payments=payments, total_paid=total_paid, total_due=total_due)


@student_bp.route('/certificates')
@login_required
@student_required
def certificates():
    student = get_student()
    certs = Certificate.query.filter_by(student_id=student.id).order_by(
        Certificate.created_at.desc()).all()
    return render_template('student/certificates.html', student=student, certificates=certs)


@student_bp.route('/timetable')
@login_required
@student_required
def timetable():
    student = get_student()
    timetable_data = {}
    if student and student.class_id:
        entries = Timetable.query.filter_by(class_id=student.class_id).all()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for day in days:
            timetable_data[day] = [e for e in entries if e.day == day]
            timetable_data[day].sort(key=lambda x: x.start_time)
    return render_template('student/timetable.html', student=student, timetable=timetable_data)


@student_bp.route('/profile')
@login_required
@student_required
def profile():
    student = get_student()
    return render_template('student/profile.html', student=student)
