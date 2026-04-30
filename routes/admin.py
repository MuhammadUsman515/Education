from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date
from sqlalchemy import func, extract
import io
import csv

from models import (db, User, Student, Teacher, Parent, Class, Subject, Department,
                    AcademicYear, Attendance, Exam, ExamResult, Certificate,
                    FeeStructure, FeePayment, Employee, LeaveRequest, Payroll, Announcement)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_students': Student.query.filter_by(status='active').count(),
        'total_teachers': Teacher.query.filter_by(status='active').count(),
        'total_classes': Class.query.count(),
        'total_staff': Employee.query.filter_by(status='active').count(),
        'pending_leaves': LeaveRequest.query.filter_by(status='pending').count(),
        'pending_fees': FeePayment.query.filter_by(status='pending').count(),
        'total_revenue': db.session.query(func.sum(FeePayment.amount_paid)).filter_by(status='paid').scalar() or 0,
        'certificates_issued': Certificate.query.filter_by(status='issued').count(),
    }

    # Gender distribution
    male_students = Student.query.filter_by(gender='Male', status='active').count()
    female_students = Student.query.filter_by(gender='Female', status='active').count()

    # Recent announcements
    announcements = Announcement.query.filter_by(is_published=True).order_by(
        Announcement.created_at.desc()).limit(5).all()

    # Recent admissions
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()

    # Monthly fee collection (last 6 months)
    fee_data = []
    from dateutil.relativedelta import relativedelta
    today = date.today()
    for i in range(5, -1, -1):
        month_date = today - relativedelta(months=i)
        month_total = db.session.query(func.sum(FeePayment.amount_paid)).filter(
            extract('month', FeePayment.payment_date) == month_date.month,
            extract('year', FeePayment.payment_date) == month_date.year,
            FeePayment.status == 'paid'
        ).scalar() or 0
        fee_data.append({'month': month_date.strftime('%b %Y'), 'amount': float(month_total)})

    return render_template('admin/dashboard.html',
                           stats=stats,
                           male_students=male_students,
                           female_students=female_students,
                           announcements=announcements,
                           recent_students=recent_students,
                           fee_data=fee_data)


# ─── Students ─────────────────────────────────────────────────────────────────

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    class_filter = request.args.get('class_id', '', type=str)
    status_filter = request.args.get('status', 'active')

    query = Student.query
    if search:
        query = query.filter(
            (Student.first_name.ilike(f'%{search}%')) |
            (Student.last_name.ilike(f'%{search}%')) |
            (Student.student_id.ilike(f'%{search}%'))
        )
    if class_filter:
        query = query.filter_by(class_id=class_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    students = query.order_by(Student.created_at.desc()).paginate(page=page, per_page=20)
    classes = Class.query.all()
    return render_template('admin/students.html', students=students, classes=classes,
                           search=search, class_filter=class_filter, status_filter=status_filter)


@admin_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    classes = Class.query.all()
    parents = Parent.query.all()

    if request.method == 'POST':
        f = request.form
        # Create user account
        username = f.get('student_id').lower()
        email = f.get('email') or f"{username}@school.edu"
        if User.query.filter_by(username=username).first():
            flash('Student ID already exists.', 'danger')
            return render_template('admin/student_form.html', classes=classes, parents=parents)

        user = User(username=username, email=email, role='student')
        user.set_password(f.get('password', 'student123'))
        db.session.add(user)
        db.session.flush()

        dob = datetime.strptime(f.get('date_of_birth'), '%Y-%m-%d').date() if f.get('date_of_birth') else None
        enrollment = datetime.strptime(f.get('enrollment_date'), '%Y-%m-%d').date() if f.get('enrollment_date') else date.today()

        student = Student(
            user_id=user.id,
            student_id=f.get('student_id'),
            first_name=f.get('first_name'),
            last_name=f.get('last_name'),
            date_of_birth=dob,
            gender=f.get('gender'),
            blood_group=f.get('blood_group'),
            address=f.get('address'),
            city=f.get('city'),
            phone=f.get('phone'),
            email=email,
            nationality=f.get('nationality', 'American'),
            religion=f.get('religion'),
            class_id=f.get('class_id') or None,
            parent_id=f.get('parent_id') or None,
            enrollment_date=enrollment,
            admission_number=f.get('admission_number'),
            previous_school=f.get('previous_school'),
        )
        db.session.add(student)
        db.session.commit()
        flash(f'Student {student.full_name} added successfully!', 'success')
        return redirect(url_for('admin.students'))

    return render_template('admin/student_form.html', classes=classes, parents=parents, student=None)


@admin_bp.route('/students/<int:student_id>')
@login_required
@admin_required
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    results = ExamResult.query.filter_by(student_id=student_id).order_by(ExamResult.created_at.desc()).all()
    attendance = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).limit(30).all()
    payments = FeePayment.query.filter_by(student_id=student_id).order_by(FeePayment.created_at.desc()).all()
    certificates = Certificate.query.filter_by(student_id=student_id).all()
    return render_template('admin/student_detail.html',
                           student=student, results=results,
                           attendance=attendance, payments=payments,
                           certificates=certificates)


@admin_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    classes = Class.query.all()
    parents = Parent.query.all()

    if request.method == 'POST':
        f = request.form
        student.first_name = f.get('first_name')
        student.last_name = f.get('last_name')
        student.gender = f.get('gender')
        student.blood_group = f.get('blood_group')
        student.address = f.get('address')
        student.city = f.get('city')
        student.phone = f.get('phone')
        student.nationality = f.get('nationality')
        student.religion = f.get('religion')
        student.class_id = f.get('class_id') or None
        student.parent_id = f.get('parent_id') or None
        student.status = f.get('status', 'active')
        if f.get('date_of_birth'):
            student.date_of_birth = datetime.strptime(f.get('date_of_birth'), '%Y-%m-%d').date()
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin.student_detail', student_id=student_id))

    return render_template('admin/student_form.html', classes=classes, parents=parents, student=student)


@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.status = 'inactive'
    db.session.commit()
    flash('Student deactivated.', 'info')
    return redirect(url_for('admin.students'))


# ─── Teachers ─────────────────────────────────────────────────────────────────

@admin_bp.route('/teachers')
@login_required
@admin_required
def teachers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    dept_filter = request.args.get('dept_id', '', type=str)

    query = Teacher.query
    if search:
        query = query.filter(
            (Teacher.first_name.ilike(f'%{search}%')) |
            (Teacher.last_name.ilike(f'%{search}%')) |
            (Teacher.teacher_id.ilike(f'%{search}%'))
        )
    if dept_filter:
        query = query.filter_by(department_id=dept_filter)

    teachers = query.order_by(Teacher.created_at.desc()).paginate(page=page, per_page=20)
    departments = Department.query.all()
    return render_template('admin/teachers.html', teachers=teachers, departments=departments,
                           search=search, dept_filter=dept_filter)


@admin_bp.route('/teachers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_teacher():
    departments = Department.query.all()

    if request.method == 'POST':
        f = request.form
        username = f.get('teacher_id').lower()
        email = f.get('email') or f"{username}@school.edu"
        if User.query.filter_by(username=username).first():
            flash('Teacher ID already exists.', 'danger')
            return render_template('admin/teacher_form.html', departments=departments)

        user = User(username=username, email=email, role='teacher')
        user.set_password(f.get('password', 'teacher123'))
        db.session.add(user)
        db.session.flush()

        dob = datetime.strptime(f.get('date_of_birth'), '%Y-%m-%d').date() if f.get('date_of_birth') else None
        joining = datetime.strptime(f.get('joining_date'), '%Y-%m-%d').date() if f.get('joining_date') else date.today()

        teacher = Teacher(
            user_id=user.id,
            teacher_id=f.get('teacher_id'),
            first_name=f.get('first_name'),
            last_name=f.get('last_name'),
            date_of_birth=dob,
            gender=f.get('gender'),
            address=f.get('address'),
            phone=f.get('phone'),
            email=email,
            qualification=f.get('qualification'),
            specialization=f.get('specialization'),
            department_id=f.get('department_id') or None,
            joining_date=joining,
            salary=float(f.get('salary', 0)),
            experience_years=int(f.get('experience_years', 0)),
        )
        db.session.add(teacher)
        db.session.commit()
        flash(f'Teacher {teacher.full_name} added successfully!', 'success')
        return redirect(url_for('admin.teachers'))

    return render_template('admin/teacher_form.html', departments=departments, teacher=None)


@admin_bp.route('/teachers/<int:teacher_id>')
@login_required
@admin_required
def teacher_detail(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    subjects = Subject.query.filter_by(teacher_id=teacher_id).all()
    exams = Exam.query.filter_by(teacher_id=teacher_id).order_by(Exam.date.desc()).limit(10).all()
    return render_template('admin/teacher_detail.html', teacher=teacher, subjects=subjects, exams=exams)


@admin_bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    departments = Department.query.all()

    if request.method == 'POST':
        f = request.form
        teacher.first_name = f.get('first_name')
        teacher.last_name = f.get('last_name')
        teacher.gender = f.get('gender')
        teacher.phone = f.get('phone')
        teacher.address = f.get('address')
        teacher.qualification = f.get('qualification')
        teacher.specialization = f.get('specialization')
        teacher.department_id = f.get('department_id') or None
        teacher.salary = float(f.get('salary', 0))
        teacher.experience_years = int(f.get('experience_years', 0))
        teacher.status = f.get('status', 'active')
        if f.get('date_of_birth'):
            teacher.date_of_birth = datetime.strptime(f.get('date_of_birth'), '%Y-%m-%d').date()
        db.session.commit()
        flash('Teacher updated successfully!', 'success')
        return redirect(url_for('admin.teacher_detail', teacher_id=teacher_id))

    return render_template('admin/teacher_form.html', departments=departments, teacher=teacher)


# ─── Classes ──────────────────────────────────────────────────────────────────

@admin_bp.route('/classes')
@login_required
@admin_required
def classes():
    classes = Class.query.order_by(Class.name).all()
    academic_years = AcademicYear.query.all()
    return render_template('admin/classes.html', classes=classes, academic_years=academic_years)


@admin_bp.route('/classes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_class():
    teachers = Teacher.query.filter_by(status='active').all()
    academic_years = AcademicYear.query.all()
    if request.method == 'POST':
        f = request.form
        cls = Class(
            name=f.get('name'),
            section=f.get('section'),
            grade=f.get('grade'),
            academic_year_id=f.get('academic_year_id') or None,
            class_teacher_id=f.get('class_teacher_id') or None,
            room_number=f.get('room_number'),
            max_students=int(f.get('max_students', 40)),
        )
        db.session.add(cls)
        db.session.commit()
        flash('Class created successfully!', 'success')
        return redirect(url_for('admin.classes'))
    return render_template('admin/class_form.html', teachers=teachers, academic_years=academic_years, cls=None)


# ─── Subjects ─────────────────────────────────────────────────────────────────

@admin_bp.route('/subjects')
@login_required
@admin_required
def subjects():
    subjects = Subject.query.order_by(Subject.name).all()
    classes = Class.query.all()
    return render_template('admin/subjects.html', subjects=subjects, classes=classes)


@admin_bp.route('/subjects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_subject():
    classes = Class.query.all()
    teachers = Teacher.query.filter_by(status='active').all()
    departments = Department.query.all()
    if request.method == 'POST':
        f = request.form
        subject = Subject(
            name=f.get('name'),
            code=f.get('code'),
            description=f.get('description'),
            class_id=f.get('class_id') or None,
            teacher_id=f.get('teacher_id') or None,
            department_id=f.get('department_id') or None,
            credit_hours=int(f.get('credit_hours', 3)),
            is_elective=bool(f.get('is_elective')),
        )
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/subject_form.html', classes=classes, teachers=teachers, departments=departments)


# ─── Departments ──────────────────────────────────────────────────────────────

@admin_bp.route('/departments')
@login_required
@admin_required
def departments():
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=departments)


@admin_bp.route('/departments/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_department():
    if request.method == 'POST':
        f = request.form
        dept = Department(name=f.get('name'), code=f.get('code'), description=f.get('description'))
        db.session.add(dept)
        db.session.commit()
        flash('Department added!', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/department_form.html')


# ─── Exams ────────────────────────────────────────────────────────────────────

@admin_bp.route('/exams')
@login_required
@admin_required
def exams():
    page = request.args.get('page', 1, type=int)
    exams = Exam.query.order_by(Exam.date.desc()).paginate(page=page, per_page=20)
    return render_template('admin/exams.html', exams=exams)


@admin_bp.route('/exams/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_exam():
    classes = Class.query.all()
    subjects = Subject.query.all()
    teachers = Teacher.query.filter_by(status='active').all()
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
            teacher_id=f.get('teacher_id') or None,
            academic_year=f.get('academic_year'),
        )
        db.session.add(exam)
        db.session.commit()
        flash('Exam scheduled successfully!', 'success')
        return redirect(url_for('admin.exams'))
    return render_template('admin/exam_form.html', classes=classes, subjects=subjects, teachers=teachers)


@admin_bp.route('/exams/<int:exam_id>/results', methods=['GET', 'POST'])
@login_required
@admin_required
def exam_results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    students = []
    if exam.class_id:
        students = Student.query.filter_by(class_id=exam.class_id, status='active').all()

    if request.method == 'POST':
        for student in students:
            marks_key = f'marks_{student.id}'
            absent_key = f'absent_{student.id}'
            marks = request.form.get(marks_key)
            is_absent = bool(request.form.get(absent_key))

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
        flash('Results saved successfully!', 'success')
        return redirect(url_for('admin.exams'))

    existing_results = {r.student_id: r for r in exam.results.all()}
    return render_template('admin/exam_results.html', exam=exam, students=students,
                           existing_results=existing_results)


# ─── Fees ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/fees')
@login_required
@admin_required
def fees():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')

    query = FeePayment.query.join(Student)
    if status_filter:
        query = query.filter(FeePayment.status == status_filter)
    if search:
        query = query.filter(
            (Student.first_name.ilike(f'%{search}%')) |
            (Student.last_name.ilike(f'%{search}%')) |
            (Student.student_id.ilike(f'%{search}%')) |
            (FeePayment.receipt_number.ilike(f'%{search}%'))
        )

    payments = query.order_by(FeePayment.created_at.desc()).paginate(page=page, per_page=20)

    total_collected = db.session.query(func.sum(FeePayment.amount_paid)).filter_by(status='paid').scalar() or 0
    total_pending = db.session.query(func.sum(FeePayment.amount_due)).filter_by(status='pending').scalar() or 0

    return render_template('admin/fees.html', payments=payments,
                           total_collected=total_collected, total_pending=total_pending,
                           status_filter=status_filter, search=search)


@admin_bp.route('/fees/structures')
@login_required
@admin_required
def fee_structures():
    structures = FeeStructure.query.filter_by(is_active=True).order_by(FeeStructure.name).all()
    classes = Class.query.all()
    return render_template('admin/fee_structures.html', structures=structures, classes=classes)


@admin_bp.route('/fees/structures/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_fee_structure():
    classes = Class.query.all()
    if request.method == 'POST':
        f = request.form
        due_date = datetime.strptime(f.get('due_date'), '%Y-%m-%d').date() if f.get('due_date') else None
        fs = FeeStructure(
            name=f.get('name'),
            class_id=f.get('class_id') or None,
            fee_type=f.get('fee_type'),
            amount=float(f.get('amount', 0)),
            frequency=f.get('frequency', 'monthly'),
            due_date=due_date,
            academic_year=f.get('academic_year'),
            description=f.get('description'),
        )
        db.session.add(fs)
        db.session.commit()
        flash('Fee structure added!', 'success')
        return redirect(url_for('admin.fee_structures'))
    return render_template('admin/fee_structure_form.html', classes=classes)


@admin_bp.route('/fees/collect', methods=['GET', 'POST'])
@login_required
@admin_required
def collect_fee():
    students = Student.query.filter_by(status='active').all()
    fee_structures = FeeStructure.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        f = request.form
        import random, string
        receipt_no = 'RCP-' + ''.join(random.choices(string.digits, k=8))
        payment_date = datetime.strptime(f.get('payment_date'), '%Y-%m-%d').date() if f.get('payment_date') else date.today()

        payment = FeePayment(
            receipt_number=receipt_no,
            student_id=int(f.get('student_id')),
            fee_structure_id=f.get('fee_structure_id') or None,
            amount_due=float(f.get('amount_due', 0)),
            amount_paid=float(f.get('amount_paid', 0)),
            discount=float(f.get('discount', 0)),
            fine=float(f.get('fine', 0)),
            payment_date=payment_date,
            payment_method=f.get('payment_method'),
            transaction_id=f.get('transaction_id'),
            status='paid' if float(f.get('amount_paid', 0)) >= float(f.get('amount_due', 0)) else 'partial',
            month=f.get('month'),
            academic_year=f.get('academic_year'),
            remarks=f.get('remarks'),
            collected_by=current_user.id,
        )
        db.session.add(payment)
        db.session.commit()
        flash(f'Fee collected! Receipt: {receipt_no}', 'success')
        return redirect(url_for('admin.fees'))

    return render_template('admin/collect_fee.html', students=students, fee_structures=fee_structures)


# ─── Certificates ─────────────────────────────────────────────────────────────

@admin_bp.route('/certificates')
@login_required
@admin_required
def certificates():
    page = request.args.get('page', 1, type=int)
    certs = Certificate.query.order_by(Certificate.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/certificates.html', certificates=certs)


@admin_bp.route('/certificates/issue', methods=['GET', 'POST'])
@login_required
@admin_required
def issue_certificate():
    students = Student.query.filter_by(status='active').all()
    if request.method == 'POST':
        f = request.form
        import random, string
        cert_no = 'CERT-' + ''.join(random.choices(string.uppercase + string.digits, k=8))
        issue_date = datetime.strptime(f.get('issue_date'), '%Y-%m-%d').date() if f.get('issue_date') else date.today()

        cert = Certificate(
            certificate_number=cert_no,
            student_id=int(f.get('student_id')),
            certificate_type=f.get('certificate_type'),
            title=f.get('title'),
            description=f.get('description'),
            issue_date=issue_date,
            issued_by=current_user.id,
            academic_year=f.get('academic_year'),
        )
        db.session.add(cert)
        db.session.commit()
        flash(f'Certificate issued! No: {cert_no}', 'success')
        return redirect(url_for('admin.certificates'))

    return render_template('admin/issue_certificate.html', students=students)


# ─── Announcements ────────────────────────────────────────────────────────────

@admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=announcements)


@admin_bp.route('/announcements/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_announcement():
    if request.method == 'POST':
        f = request.form
        ann = Announcement(
            title=f.get('title'),
            content=f.get('content'),
            target_audience=f.get('target_audience', 'all'),
            priority=f.get('priority', 'normal'),
            is_published=bool(f.get('is_published')),
            created_by=current_user.id,
        )
        db.session.add(ann)
        db.session.commit()
        flash('Announcement published!', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/announcement_form.html')


# ─── Reports ──────────────────────────────────────────────────────────────────

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('admin/reports.html')


@admin_bp.route('/reports/students/export')
@login_required
@admin_required
def export_students():
    students = Student.query.filter_by(status='active').all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'First Name', 'Last Name', 'Gender', 'Class',
                     'Parent', 'Phone', 'Email', 'Status', 'Enrollment Date'])
    for s in students:
        writer.writerow([
            s.student_id, s.first_name, s.last_name, s.gender or '',
            s.current_class.full_name if s.current_class else '',
            s.parent.full_name if s.parent else '',
            s.phone or '', s.email or '', s.status,
            s.enrollment_date.strftime('%Y-%m-%d') if s.enrollment_date else '',
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='students_report.csv'
    )


@admin_bp.route('/reports/fees/export')
@login_required
@admin_required
def export_fees():
    payments = FeePayment.query.join(Student).order_by(FeePayment.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Receipt No', 'Student', 'Student ID', 'Amount Due', 'Amount Paid',
                     'Discount', 'Balance', 'Method', 'Date', 'Status', 'Month'])
    for p in payments:
        writer.writerow([
            p.receipt_number,
            p.student.full_name,
            p.student.student_id,
            p.amount_due, p.amount_paid,
            p.discount, p.balance,
            p.payment_method or '',
            p.payment_date.strftime('%Y-%m-%d') if p.payment_date else '',
            p.status, p.month or '',
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='fees_report.csv'
    )


# ─── Users Management ─────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Can't deactivate your own account.", 'warning')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f"User {'activated' if user.is_active else 'deactivated'} successfully.", 'success')
    return redirect(url_for('admin.users'))


# ─── Academic Years ───────────────────────────────────────────────────────────

@admin_bp.route('/academic-years')
@login_required
@admin_required
def academic_years():
    years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
    return render_template('admin/academic_years.html', years=years)


@admin_bp.route('/academic-years/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_academic_year():
    if request.method == 'POST':
        f = request.form
        if f.get('is_current'):
            AcademicYear.query.update({'is_current': False})
        year = AcademicYear(
            name=f.get('name'),
            start_date=datetime.strptime(f.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(f.get('end_date'), '%Y-%m-%d').date(),
            is_current=bool(f.get('is_current')),
        )
        db.session.add(year)
        db.session.commit()
        flash('Academic year added!', 'success')
        return redirect(url_for('admin.academic_years'))
    return render_template('admin/academic_year_form.html')
