from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import date, datetime

from models import (db, Teacher, Student, Subject, Class, Attendance,
                    Exam, ExamResult, Announcement, Timetable)

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Teacher access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def get_teacher():
    return Teacher.query.filter_by(user_id=current_user.id).first()


@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    teacher = get_teacher()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    classes_ids = list({s.class_id for s in subjects if s.class_id})
    total_students = Student.query.filter(
        Student.class_id.in_(classes_ids), Student.status == 'active'
    ).count() if classes_ids else 0

    upcoming_exams = Exam.query.filter_by(teacher_id=teacher.id, status='scheduled').filter(
        Exam.date >= date.today()
    ).order_by(Exam.date).limit(5).all()

    recent_exams = Exam.query.filter_by(teacher_id=teacher.id).order_by(
        Exam.created_at.desc()).limit(5).all()

    announcements = Announcement.query.filter(
        Announcement.target_audience.in_(['all', 'teachers']),
        Announcement.is_published == True
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    return render_template('teacher/dashboard.html',
                           teacher=teacher,
                           subjects=subjects,
                           total_students=total_students,
                           upcoming_exams=upcoming_exams,
                           recent_exams=recent_exams,
                           announcements=announcements)


@teacher_bp.route('/classes')
@login_required
@teacher_required
def classes():
    teacher = get_teacher()
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    class_ids = list({s.class_id for s in subjects if s.class_id})
    classes = Class.query.filter(Class.id.in_(class_ids)).all() if class_ids else []
    return render_template('teacher/classes.html', teacher=teacher, classes=classes, subjects=subjects)


@teacher_bp.route('/classes/<int:class_id>/students')
@login_required
@teacher_required
def class_students(class_id):
    teacher = get_teacher()
    cls = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id, status='active').all()
    return render_template('teacher/class_students.html', teacher=teacher, cls=cls, students=students)


@teacher_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def attendance():
    teacher = get_teacher()
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    selected_subject = None
    students = []
    existing = {}
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))

    subject_id = request.args.get('subject_id', type=int)
    if subject_id:
        selected_subject = Subject.query.get(subject_id)
        if selected_subject and selected_subject.class_id:
            students = Student.query.filter_by(class_id=selected_subject.class_id, status='active').all()
            att_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            records = Attendance.query.filter_by(subject_id=subject_id, date=att_date).all()
            existing = {r.student_id: r for r in records}

    if request.method == 'POST':
        subject_id = int(request.form.get('subject_id'))
        att_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        subject = Subject.query.get(subject_id)
        students_in_class = Student.query.filter_by(class_id=subject.class_id, status='active').all()

        for student in students_in_class:
            status = request.form.get(f'status_{student.id}', 'absent')
            remarks = request.form.get(f'remarks_{student.id}', '')
            existing_rec = Attendance.query.filter_by(
                student_id=student.id, subject_id=subject_id, date=att_date).first()
            if existing_rec:
                existing_rec.status = status
                existing_rec.remarks = remarks
            else:
                rec = Attendance(
                    student_id=student.id,
                    subject_id=subject_id,
                    class_id=subject.class_id,
                    date=att_date,
                    status=status,
                    remarks=remarks,
                    marked_by=current_user.id,
                )
                db.session.add(rec)
        db.session.commit()
        flash('Attendance saved successfully!', 'success')
        return redirect(url_for('teacher.attendance', subject_id=subject_id, date=att_date))

    return render_template('teacher/attendance.html',
                           teacher=teacher, subjects=subjects,
                           selected_subject=selected_subject,
                           students=students, existing=existing,
                           selected_date=selected_date)


@teacher_bp.route('/exams')
@login_required
@teacher_required
def exams():
    teacher = get_teacher()
    exams = Exam.query.filter_by(teacher_id=teacher.id).order_by(Exam.date.desc()).all()
    return render_template('teacher/exams.html', teacher=teacher, exams=exams)


@teacher_bp.route('/exams/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_exam():
    teacher = get_teacher()
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    class_ids = list({s.class_id for s in subjects if s.class_id})
    classes = Class.query.filter(Class.id.in_(class_ids)).all() if class_ids else []

    if request.method == 'POST':
        f = request.form
        exam_date = datetime.strptime(f.get('date'), '%Y-%m-%d').date() if f.get('date') else None
        exam = Exam(
            name=f.get('name'),
            exam_type=f.get('exam_type'),
            subject_id=f.get('subject_id') or None,
            class_id=f.get('class_id') or None,
            date=exam_date,
            duration_minutes=int(f.get('duration_minutes', 60)),
            total_marks=float(f.get('total_marks', 100)),
            passing_marks=float(f.get('passing_marks', 40)),
            instructions=f.get('instructions'),
            teacher_id=teacher.id,
            created_by=current_user.id,
        )
        db.session.add(exam)
        db.session.commit()
        flash('Exam created successfully!', 'success')
        return redirect(url_for('teacher.exams'))

    return render_template('teacher/create_exam.html', teacher=teacher, subjects=subjects, classes=classes)


@teacher_bp.route('/exams/<int:exam_id>/grade', methods=['GET', 'POST'])
@login_required
@teacher_required
def grade_exam(exam_id):
    teacher = get_teacher()
    exam = Exam.query.get_or_404(exam_id)
    students = []
    if exam.class_id:
        students = Student.query.filter_by(class_id=exam.class_id, status='active').all()

    if request.method == 'POST':
        for student in students:
            marks = request.form.get(f'marks_{student.id}')
            is_absent = bool(request.form.get(f'absent_{student.id}'))
            existing = ExamResult.query.filter_by(exam_id=exam_id, student_id=student.id).first()
            if not existing:
                existing = ExamResult(exam_id=exam_id, student_id=student.id, entered_by=current_user.id)
                db.session.add(existing)
            existing.is_absent = is_absent
            if not is_absent and marks:
                m = float(marks)
                existing.marks_obtained = m
                grade, gp = ExamResult.calculate_grade(m, exam.total_marks)
                existing.grade = grade
                existing.grade_points = gp
            existing.remarks = request.form.get(f'remarks_{student.id}', '')
        exam.status = 'completed'
        db.session.commit()
        flash('Grades saved successfully!', 'success')
        return redirect(url_for('teacher.exams'))

    existing_results = {r.student_id: r for r in exam.results.all()}
    return render_template('teacher/grade_exam.html',
                           teacher=teacher, exam=exam,
                           students=students, existing_results=existing_results)


@teacher_bp.route('/timetable')
@login_required
@teacher_required
def timetable():
    teacher = get_teacher()
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    subject_ids = [s.id for s in subjects]
    entries = Timetable.query.filter(Timetable.subject_id.in_(subject_ids)).all() if subject_ids else []
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable_data = {day: [e for e in entries if e.day == day] for day in days}
    for day in days:
        timetable_data[day].sort(key=lambda x: x.start_time)
    return render_template('teacher/timetable.html', teacher=teacher, timetable=timetable_data)


@teacher_bp.route('/profile')
@login_required
@teacher_required
def profile():
    teacher = get_teacher()
    return render_template('teacher/profile.html', teacher=teacher)
