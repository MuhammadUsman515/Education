from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─── Core Auth ────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    # roles: admin | teacher | student | parent | hr
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='user', uselist=False, lazy='joined')
    teacher = db.relationship('Teacher', back_populates='user', uselist=False, lazy='joined')
    parent = db.relationship('Parent', back_populates='user', uselist=False, lazy='joined')
    employee = db.relationship('Employee', back_populates='user', uselist=False, lazy='joined')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        if self.student:
            return f"{self.student.first_name} {self.student.last_name}"
        if self.teacher:
            return f"{self.teacher.first_name} {self.teacher.last_name}"
        if self.parent:
            return f"{self.parent.first_name} {self.parent.last_name}"
        if self.employee:
            return f"{self.employee.first_name} {self.employee.last_name}"
        return self.username

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


# ─── Academic Structure ────────────────────────────────────────────────────────

class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)  # e.g. 2024-2025
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    classes = db.relationship('Class', back_populates='academic_year', lazy='dynamic')

    def __repr__(self):
        return f'<AcademicYear {self.name}>'


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teachers = db.relationship('Teacher', back_populates='department', lazy='dynamic')
    employees = db.relationship('Employee', back_populates='department', lazy='dynamic')
    subjects = db.relationship('Subject', back_populates='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.name}>'


class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'))
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    room_number = db.Column(db.String(20))
    max_students = db.Column(db.Integer, default=40)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    academic_year = db.relationship('AcademicYear', back_populates='classes')
    class_teacher = db.relationship('Teacher', foreign_keys=[class_teacher_id], back_populates='class_managed')
    students = db.relationship('Student', back_populates='current_class', lazy='dynamic')
    subjects = db.relationship('Subject', back_populates='class_', lazy='dynamic')
    exams = db.relationship('Exam', back_populates='class_', lazy='dynamic')
    timetable = db.relationship('Timetable', back_populates='class_', lazy='dynamic')
    fee_structures = db.relationship('FeeStructure', back_populates='class_', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.name} - {self.section}"

    def __repr__(self):
        return f'<Class {self.name}-{self.section}>'


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    credit_hours = db.Column(db.Integer, default=3)
    is_elective = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    class_ = db.relationship('Class', back_populates='subjects')
    teacher = db.relationship('Teacher', back_populates='subjects', foreign_keys=[teacher_id])
    department = db.relationship('Department', back_populates='subjects')
    attendance_records = db.relationship('Attendance', back_populates='subject', lazy='dynamic')
    exams = db.relationship('Exam', back_populates='subject', lazy='dynamic')
    timetable = db.relationship('Timetable', back_populates='subject', lazy='dynamic')

    def __repr__(self):
        return f'<Subject {self.code}: {self.name}>'


# ─── People ───────────────────────────────────────────────────────────────────

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(20))
    email = db.Column(db.String(120))
    photo = db.Column(db.String(200), default='default_student.png')
    nationality = db.Column(db.String(50), default='American')
    religion = db.Column(db.String(50))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=True)
    enrollment_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='active')
    # status: active | graduated | transferred | suspended | expelled
    admission_number = db.Column(db.String(30), unique=True)
    previous_school = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='student')
    current_class = db.relationship('Class', back_populates='students')
    parent = db.relationship('Parent', back_populates='children')
    attendance_records = db.relationship('Attendance', back_populates='student', lazy='dynamic')
    exam_results = db.relationship('ExamResult', back_populates='student', lazy='dynamic')
    certificates = db.relationship('Certificate', back_populates='student', lazy='dynamic')
    fee_payments = db.relationship('FeePayment', back_populates='student', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def attendance_percentage(self, subject_id=None):
        query = self.attendance_records
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        total = query.count()
        if total == 0:
            return 0
        present = query.filter(Attendance.status.in_(['present', 'late'])).count()
        return round((present / total) * 100, 1)

    def __repr__(self):
        return f'<Student {self.student_id}: {self.full_name}>'


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    teacher_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    photo = db.Column(db.String(200), default='default_teacher.png')
    qualification = db.Column(db.String(200))
    specialization = db.Column(db.String(200))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    joining_date = db.Column(db.Date, default=date.today)
    salary = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')
    experience_years = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='teacher')
    department = db.relationship('Department', back_populates='teachers')
    subjects = db.relationship('Subject', back_populates='teacher',
                               foreign_keys='Subject.teacher_id', lazy='dynamic')
    class_managed = db.relationship('Class', back_populates='class_teacher',
                                    foreign_keys='Class.class_teacher_id', lazy='dynamic')
    exams_created = db.relationship('Exam', back_populates='created_by_teacher', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Teacher {self.teacher_id}: {self.full_name}>'


class Parent(db.Model):
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    alternate_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    occupation = db.Column(db.String(100))
    relationship_to_student = db.Column(db.String(30), default='parent')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='parent')
    children = db.relationship('Student', back_populates='parent', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Parent {self.full_name}>'


# ─── Attendance ───────────────────────────────────────────────────────────────

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='present')
    # status: present | absent | late | excused
    remarks = db.Column(db.String(200))
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='attendance_records')
    subject = db.relationship('Subject', back_populates='attendance_records')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'date', name='unique_attendance'),
    )

    def __repr__(self):
        return f'<Attendance {self.student_id} {self.date} {self.status}>'


# ─── Exams & Results ──────────────────────────────────────────────────────────

class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(30), nullable=False)
    # type: midterm | final | quiz | assignment | practical
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer, default=60)
    total_marks = db.Column(db.Float, nullable=False, default=100)
    passing_marks = db.Column(db.Float, nullable=False, default=40)
    instructions = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')
    # status: scheduled | ongoing | completed | cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    academic_year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship('Subject', back_populates='exams')
    class_ = db.relationship('Class', back_populates='exams')
    created_by_teacher = db.relationship('Teacher', back_populates='exams_created',
                                          foreign_keys=[teacher_id])
    results = db.relationship('ExamResult', back_populates='exam', lazy='dynamic')

    def __repr__(self):
        return f'<Exam {self.name}>'


class ExamResult(db.Model):
    __tablename__ = 'exam_results'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    marks_obtained = db.Column(db.Float)
    grade = db.Column(db.String(5))
    grade_points = db.Column(db.Float)
    remarks = db.Column(db.String(200))
    is_absent = db.Column(db.Boolean, default=False)
    entered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam = db.relationship('Exam', back_populates='results')
    student = db.relationship('Student', back_populates='exam_results')

    __table_args__ = (
        db.UniqueConstraint('exam_id', 'student_id', name='unique_exam_result'),
    )

    @staticmethod
    def calculate_grade(marks, total):
        percentage = (marks / total) * 100
        if percentage >= 90:
            return 'A+', 4.0
        elif percentage >= 80:
            return 'A', 3.7
        elif percentage >= 70:
            return 'B+', 3.3
        elif percentage >= 60:
            return 'B', 3.0
        elif percentage >= 50:
            return 'C+', 2.3
        elif percentage >= 40:
            return 'C', 2.0
        elif percentage >= 33:
            return 'D', 1.0
        else:
            return 'F', 0.0

    def __repr__(self):
        return f'<ExamResult exam={self.exam_id} student={self.student_id}>'


# ─── Certificates ─────────────────────────────────────────────────────────────

class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer, primary_key=True)
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    certificate_type = db.Column(db.String(50), nullable=False)
    # type: completion | merit | sports | participation | conduct | transfer
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    issue_date = db.Column(db.Date, default=date.today)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='issued')
    # status: issued | revoked | pending
    academic_year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='certificates')

    def __repr__(self):
        return f'<Certificate {self.certificate_number}>'


# ─── Fees & Finance ───────────────────────────────────────────────────────────

class FeeStructure(db.Model):
    __tablename__ = 'fee_structures'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    fee_type = db.Column(db.String(50), nullable=False)
    # type: tuition | admission | exam | library | sports | transport | hostel | lab
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), default='monthly')
    # frequency: monthly | quarterly | yearly | one-time
    due_date = db.Column(db.Date)
    academic_year = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    class_ = db.relationship('Class', back_populates='fee_structures')
    payments = db.relationship('FeePayment', back_populates='fee_structure', lazy='dynamic')

    def __repr__(self):
        return f'<FeeStructure {self.name}>'


class FeePayment(db.Model):
    __tablename__ = 'fee_payments'
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=True)
    amount_due = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False, default=0)
    discount = db.Column(db.Float, default=0)
    fine = db.Column(db.Float, default=0)
    payment_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    payment_method = db.Column(db.String(30))
    # method: cash | bank_transfer | online | cheque | card
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    # status: paid | partial | pending | overdue | waived
    remarks = db.Column(db.String(200))
    collected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    month = db.Column(db.String(20))
    academic_year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='fee_payments')
    fee_structure = db.relationship('FeeStructure', back_populates='payments')

    @property
    def balance(self):
        return self.amount_due - self.amount_paid - self.discount + self.fine

    def __repr__(self):
        return f'<FeePayment {self.receipt_number}>'


# ─── HR & Payroll ─────────────────────────────────────────────────────────────

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    photo = db.Column(db.String(200), default='default_employee.png')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    designation = db.Column(db.String(100))
    employment_type = db.Column(db.String(30), default='full-time')
    # type: full-time | part-time | contract | temporary
    joining_date = db.Column(db.Date, default=date.today)
    basic_salary = db.Column(db.Float, default=0.0)
    bank_account = db.Column(db.String(50))
    national_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')
    # status: active | inactive | terminated | resigned | retired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='employee')
    department = db.relationship('Department', back_populates='employees')
    leave_requests = db.relationship('LeaveRequest', back_populates='employee', lazy='dynamic')
    payroll_records = db.relationship('Payroll', back_populates='employee', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.full_name}>'


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)
    # type: annual | sick | maternity | paternity | unpaid | emergency | study
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    # status: pending | approved | rejected | cancelled
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='leave_requests')

    def __repr__(self):
        return f'<LeaveRequest {self.employee_id} {self.leave_type}>'


class Payroll(db.Model):
    __tablename__ = 'payroll'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    basic_salary = db.Column(db.Float, nullable=False)
    house_allowance = db.Column(db.Float, default=0)
    transport_allowance = db.Column(db.Float, default=0)
    medical_allowance = db.Column(db.Float, default=0)
    other_allowances = db.Column(db.Float, default=0)
    tax_deduction = db.Column(db.Float, default=0)
    pension_deduction = db.Column(db.Float, default=0)
    other_deductions = db.Column(db.Float, default=0)
    overtime_hours = db.Column(db.Float, default=0)
    overtime_amount = db.Column(db.Float, default=0)
    gross_salary = db.Column(db.Float)
    net_salary = db.Column(db.Float)
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(30), default='bank_transfer')
    status = db.Column(db.String(20), default='pending')
    # status: pending | paid | cancelled
    remarks = db.Column(db.Text)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='payroll_records')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year', name='unique_payroll'),
    )

    def calculate(self):
        allowances = ((self.house_allowance or 0) + (self.transport_allowance or 0) +
                      (self.medical_allowance or 0) + (self.other_allowances or 0) + (self.overtime_amount or 0))
        deductions = (self.tax_deduction or 0) + (self.pension_deduction or 0) + (self.other_deductions or 0)
        self.gross_salary = self.basic_salary + allowances
        self.net_salary = self.gross_salary - deductions

    def __repr__(self):
        return f'<Payroll {self.employee_id} {self.month}/{self.year}>'


# ─── Timetable ────────────────────────────────────────────────────────────────

class Timetable(db.Model):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    # day: Monday | Tuesday | Wednesday | Thursday | Friday | Saturday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    class_ = db.relationship('Class', back_populates='timetable')
    subject = db.relationship('Subject', back_populates='timetable')

    def __repr__(self):
        return f'<Timetable {self.class_id} {self.day}>'


# ─── Announcements ────────────────────────────────────────────────────────────

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    target_audience = db.Column(db.String(50), default='all')
    # target: all | students | teachers | parents | staff
    priority = db.Column(db.String(20), default='normal')
    # priority: low | normal | high | urgent
    is_published = db.Column(db.Boolean, default=True)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Announcement {self.title}>'
