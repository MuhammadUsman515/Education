from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date
from sqlalchemy import func
import io, csv

from models import (db, Employee, Department, LeaveRequest, Payroll,
                    User, Teacher, Announcement)

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')


def hr_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'hr'):
            flash('HR access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@hr_bp.route('/dashboard')
@login_required
@hr_required
def dashboard():
    stats = {
        'total_employees': Employee.query.filter_by(status='active').count(),
        'teachers': Employee.query.join(Department).filter_by(status='active').count(),
        'pending_leaves': LeaveRequest.query.filter_by(status='pending').count(),
        'departments': Department.query.count(),
    }

    pending_leaves = LeaveRequest.query.filter_by(status='pending').order_by(
        LeaveRequest.created_at.desc()).limit(5).all()
    recent_employees = Employee.query.filter_by(status='active').order_by(
        Employee.created_at.desc()).limit(5).all()

    # Monthly payroll total
    today = date.today()
    monthly_payroll = db.session.query(func.sum(Payroll.net_salary)).filter(
        Payroll.month == today.month,
        Payroll.year == today.year,
    ).scalar() or 0

    # Department-wise headcount
    dept_data = db.session.query(
        Department.name,
        func.count(Employee.id).label('count')
    ).join(Employee, Employee.department_id == Department.id).filter(
        Employee.status == 'active'
    ).group_by(Department.name).all()

    return render_template('hr/dashboard.html',
                           stats=stats,
                           pending_leaves=pending_leaves,
                           recent_employees=recent_employees,
                           monthly_payroll=monthly_payroll,
                           dept_data=dept_data)


# ─── Employees ────────────────────────────────────────────────────────────────

@hr_bp.route('/employees')
@login_required
@hr_required
def employees():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    dept_filter = request.args.get('dept_id', '')

    query = Employee.query
    if search:
        query = query.filter(
            (Employee.first_name.ilike(f'%{search}%')) |
            (Employee.last_name.ilike(f'%{search}%')) |
            (Employee.employee_id.ilike(f'%{search}%'))
        )
    if dept_filter:
        query = query.filter_by(department_id=dept_filter)

    employees = query.order_by(Employee.created_at.desc()).paginate(page=page, per_page=20)
    departments = Department.query.all()
    return render_template('hr/employees.html', employees=employees, departments=departments,
                           search=search, dept_filter=dept_filter)


@hr_bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
@hr_required
def add_employee():
    departments = Department.query.all()
    if request.method == 'POST':
        f = request.form
        username = f.get('employee_id').lower()
        email = f.get('email') or f"{username}@school.edu"
        if User.query.filter_by(username=username).first():
            flash('Employee ID already exists.', 'danger')
            return render_template('hr/employee_form.html', departments=departments)

        user = User(username=username, email=email, role='hr')
        user.set_password(f.get('password', 'staff123'))
        db.session.add(user)
        db.session.flush()

        dob = datetime.strptime(f.get('date_of_birth'), '%Y-%m-%d').date() if f.get('date_of_birth') else None
        joining = datetime.strptime(f.get('joining_date'), '%Y-%m-%d').date() if f.get('joining_date') else date.today()

        emp = Employee(
            user_id=user.id,
            employee_id=f.get('employee_id'),
            first_name=f.get('first_name'),
            last_name=f.get('last_name'),
            date_of_birth=dob,
            gender=f.get('gender'),
            phone=f.get('phone'),
            email=email,
            address=f.get('address'),
            department_id=f.get('department_id') or None,
            designation=f.get('designation'),
            employment_type=f.get('employment_type', 'full-time'),
            joining_date=joining,
            basic_salary=float(f.get('basic_salary', 0)),
            bank_account=f.get('bank_account'),
            national_id=f.get('national_id'),
        )
        db.session.add(emp)
        db.session.commit()
        flash(f'Employee {emp.full_name} added!', 'success')
        return redirect(url_for('hr.employees'))

    return render_template('hr/employee_form.html', departments=departments, employee=None)


@hr_bp.route('/employees/<int:emp_id>')
@login_required
@hr_required
def employee_detail(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    leaves = LeaveRequest.query.filter_by(employee_id=emp_id).order_by(
        LeaveRequest.created_at.desc()).limit(10).all()
    payroll = Payroll.query.filter_by(employee_id=emp_id).order_by(
        Payroll.year.desc(), Payroll.month.desc()).limit(12).all()
    return render_template('hr/employee_detail.html',
                           employee=employee, leaves=leaves, payroll=payroll)


@hr_bp.route('/employees/<int:emp_id>/edit', methods=['GET', 'POST'])
@login_required
@hr_required
def edit_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    departments = Department.query.all()
    if request.method == 'POST':
        f = request.form
        employee.first_name = f.get('first_name')
        employee.last_name = f.get('last_name')
        employee.gender = f.get('gender')
        employee.phone = f.get('phone')
        employee.address = f.get('address')
        employee.department_id = f.get('department_id') or None
        employee.designation = f.get('designation')
        employee.employment_type = f.get('employment_type', 'full-time')
        employee.basic_salary = float(f.get('basic_salary', 0))
        employee.bank_account = f.get('bank_account')
        employee.status = f.get('status', 'active')
        db.session.commit()
        flash('Employee updated!', 'success')
        return redirect(url_for('hr.employee_detail', emp_id=emp_id))
    return render_template('hr/employee_form.html', departments=departments, employee=employee)


# ─── Leave Requests ───────────────────────────────────────────────────────────

@hr_bp.route('/leaves')
@login_required
@hr_required
def leaves():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = LeaveRequest.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    leaves = query.order_by(LeaveRequest.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('hr/leaves.html', leaves=leaves, status_filter=status_filter)


@hr_bp.route('/leaves/<int:leave_id>/action', methods=['POST'])
@login_required
@hr_required
def action_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    action = request.form.get('action')
    remarks = request.form.get('remarks', '')
    if action in ('approved', 'rejected'):
        leave.status = action
        leave.approved_by = current_user.id
        leave.approved_at = datetime.utcnow()
        leave.remarks = remarks
        db.session.commit()
        flash(f'Leave request {action} successfully.', 'success')
    return redirect(url_for('hr.leaves'))


# ─── Payroll ──────────────────────────────────────────────────────────────────

@hr_bp.route('/payroll')
@login_required
@hr_required
def payroll():
    page = request.args.get('page', 1, type=int)
    month_filter = request.args.get('month', date.today().month, type=int)
    year_filter = request.args.get('year', date.today().year, type=int)

    records = Payroll.query.filter_by(month=month_filter, year=year_filter).order_by(
        Payroll.created_at.desc()).paginate(page=page, per_page=20)

    total_gross = db.session.query(func.sum(Payroll.gross_salary)).filter_by(
        month=month_filter, year=year_filter).scalar() or 0
    total_net = db.session.query(func.sum(Payroll.net_salary)).filter_by(
        month=month_filter, year=year_filter).scalar() or 0

    return render_template('hr/payroll.html', records=records,
                           month_filter=month_filter, year_filter=year_filter,
                           total_gross=total_gross, total_net=total_net)


@hr_bp.route('/payroll/generate', methods=['GET', 'POST'])
@login_required
@hr_required
def generate_payroll():
    employees = Employee.query.filter_by(status='active').all()
    if request.method == 'POST':
        f = request.form
        month = int(f.get('month'))
        year = int(f.get('year'))
        generated = 0
        for emp in employees:
            existing = Payroll.query.filter_by(employee_id=emp.id, month=month, year=year).first()
            if not existing:
                p = Payroll(
                    employee_id=emp.id,
                    month=month,
                    year=year,
                    basic_salary=emp.basic_salary,
                    house_allowance=emp.basic_salary * 0.2,
                    transport_allowance=emp.basic_salary * 0.1,
                    medical_allowance=emp.basic_salary * 0.05,
                    tax_deduction=emp.basic_salary * 0.1,
                    pension_deduction=emp.basic_salary * 0.05,
                    processed_by=current_user.id,
                )
                p.calculate()
                db.session.add(p)
                generated += 1
        db.session.commit()
        flash(f'Payroll generated for {generated} employees!', 'success')
        return redirect(url_for('hr.payroll', month=month, year=year))

    return render_template('hr/generate_payroll.html', employees=employees)


@hr_bp.route('/payroll/<int:payroll_id>/pay', methods=['POST'])
@login_required
@hr_required
def mark_paid(payroll_id):
    record = Payroll.query.get_or_404(payroll_id)
    record.status = 'paid'
    record.payment_date = date.today()
    db.session.commit()
    flash('Payroll marked as paid.', 'success')
    return redirect(url_for('hr.payroll'))


@hr_bp.route('/payroll/export')
@login_required
@hr_required
def export_payroll():
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    records = Payroll.query.filter_by(month=month, year=year).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Employee ID', 'Name', 'Department', 'Basic Salary',
                     'House Allowance', 'Transport', 'Medical', 'Overtime',
                     'Tax', 'Pension', 'Gross', 'Net', 'Status'])
    for r in records:
        writer.writerow([
            r.employee.employee_id, r.employee.full_name,
            r.employee.department.name if r.employee.department else '',
            r.basic_salary, r.house_allowance, r.transport_allowance,
            r.medical_allowance, r.overtime_amount,
            r.tax_deduction, r.pension_deduction,
            r.gross_salary, r.net_salary, r.status,
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'payroll_{month}_{year}.csv'
    )
