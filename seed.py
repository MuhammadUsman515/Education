"""
EduManage Pro — Sample Data Seeder
Run: python seed.py
"""

from app import app, db
from models import (User, AcademicYear, Department, Class, Subject, Student,
                    Teacher, Parent, Employee, Attendance, Exam, ExamResult,
                    Certificate, FeeStructure, FeePayment, LeaveRequest, Payroll,
                    Announcement, Timetable)
from datetime import date, datetime, time
from werkzeug.security import generate_password_hash
import random
import string


def seed():
    with app.app_context():
        print("Dropping and recreating tables…")
        db.drop_all()
        db.create_all()

        print("Seeding Academic Years…")
        ay = AcademicYear(name='2024-2025',
                          start_date=date(2024, 8, 1),
                          end_date=date(2025, 6, 30),
                          is_current=True)
        db.session.add(ay)
        db.session.flush()

        print("Seeding Departments…")
        depts = []
        for name, code in [
            ('Mathematics', 'DEPT-MATH'),
            ('Science', 'DEPT-SCI'),
            ('English', 'DEPT-ENG'),
            ('Social Studies', 'DEPT-SOC'),
            ('Computer Science', 'DEPT-CS'),
            ('Physical Education', 'DEPT-PE'),
            ('Administration', 'DEPT-ADM'),
            ('Finance', 'DEPT-FIN'),
        ]:
            d = Department(name=name, code=code)
            db.session.add(d)
            depts.append(d)
        db.session.flush()

        print("Seeding Admin user…")
        admin_user = User(username='admin', email='admin@school.edu', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.flush()

        print("Seeding Teachers…")
        teacher_data = [
            ('John', 'Smith', 'M.Sc Mathematics', 'Mathematics', depts[0].id, 5500),
            ('Sarah', 'Johnson', 'M.Sc Physics', 'Science', depts[1].id, 5200),
            ('Emily', 'Davis', 'M.A English', 'English Literature', depts[2].id, 4800),
            ('Michael', 'Brown', 'M.A History', 'Social Studies', depts[3].id, 4900),
            ('David', 'Wilson', 'M.Tech CS', 'Computer Science', depts[4].id, 6000),
        ]
        teachers = []
        for i, (fn, ln, qual, spec, dept_id, sal) in enumerate(teacher_data, 1):
            t_id = f'T{i:03d}'
            email = f'teacher{i:03d}@school.edu'
            user = User(username=f'teacher{i:03d}', email=email, role='teacher')
            user.set_password('teacher123')
            db.session.add(user)
            db.session.flush()
            t = Teacher(
                user_id=user.id,
                teacher_id=t_id,
                first_name=fn,
                last_name=ln,
                gender='Male' if i % 2 == 0 else 'Female',
                email=email,
                phone=f'+1-555-{1000+i}',
                qualification=qual,
                specialization=spec,
                department_id=dept_id,
                joining_date=date(2020, 1, i * 2),
                salary=sal,
                experience_years=random.randint(2, 15),
            )
            db.session.add(t)
            teachers.append(t)
        db.session.flush()

        print("Seeding Classes…")
        classes = []
        class_data = [
            ('Grade 9', 'A', '9'), ('Grade 9', 'B', '9'),
            ('Grade 10', 'A', '10'), ('Grade 10', 'B', '10'),
            ('Grade 11', 'A', '11'), ('Grade 12', 'A', '12'),
        ]
        for i, (name, section, grade) in enumerate(class_data):
            cls = Class(
                name=name,
                section=section,
                grade=grade,
                academic_year_id=ay.id,
                class_teacher_id=teachers[i % len(teachers)].id,
                room_number=f'Room {101 + i}',
                max_students=35,
            )
            db.session.add(cls)
            classes.append(cls)
        db.session.flush()

        print("Seeding Subjects…")
        subjects = []
        subject_data = [
            ('Mathematics', 'MATH101', teachers[0], classes[0]),
            ('Physics', 'PHY101', teachers[1], classes[0]),
            ('English', 'ENG101', teachers[2], classes[0]),
            ('History', 'HIS101', teachers[3], classes[0]),
            ('Computer Science', 'CS101', teachers[4], classes[0]),
            ('Mathematics', 'MATH201', teachers[0], classes[2]),
            ('Chemistry', 'CHE201', teachers[1], classes[2]),
            ('English', 'ENG201', teachers[2], classes[2]),
            ('Computer Science', 'CS201', teachers[4], classes[2]),
            ('Mathematics', 'MATH301', teachers[0], classes[4]),
            ('Physics', 'PHY301', teachers[1], classes[4]),
            ('Computer Science', 'CS301', teachers[4], classes[4]),
        ]
        for name, code, teacher, cls in subject_data:
            s = Subject(
                name=name,
                code=code,
                teacher_id=teacher.id,
                class_id=cls.id,
                department_id=teacher.department_id,
                credit_hours=3,
            )
            db.session.add(s)
            subjects.append(s)
        db.session.flush()

        print("Seeding Timetable…")
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for idx, subj in enumerate(subjects[:5]):
            tt = Timetable(
                class_id=subj.class_id,
                subject_id=subj.id,
                day=days[idx % 5],
                start_time=time(8 + idx, 0),
                end_time=time(9 + idx, 0),
                room=f'Room {101 + idx}',
            )
            db.session.add(tt)
        db.session.flush()

        print("Seeding Parents…")
        parents = []
        parent_names = [
            ('Robert', 'Anderson'), ('Linda', 'Martinez'), ('James', 'Taylor'),
            ('Patricia', 'Thomas'), ('Charles', 'Jackson'), ('Barbara', 'White'),
            ('Steven', 'Harris'), ('Susan', 'Clark'), ('Kenneth', 'Lewis'),
            ('Margaret', 'Robinson'),
        ]
        for i, (fn, ln) in enumerate(parent_names, 1):
            email = f'parent{i:03d}@email.com'
            user = User(username=f'parent{i:03d}', email=email, role='parent')
            user.set_password('parent123')
            db.session.add(user)
            db.session.flush()
            p = Parent(
                user_id=user.id,
                first_name=fn,
                last_name=ln,
                email=email,
                phone=f'+1-555-{2000+i}',
                occupation=random.choice(['Engineer', 'Doctor', 'Teacher', 'Business Owner', 'Accountant']),
            )
            db.session.add(p)
            parents.append(p)
        db.session.flush()

        print("Seeding Students…")
        first_names_m = ['James', 'John', 'Alex', 'Ryan', 'Ethan', 'Noah', 'Liam', 'Mason', 'Lucas', 'Oliver']
        first_names_f = ['Emma', 'Olivia', 'Ava', 'Isabella', 'Sophia', 'Mia', 'Charlotte', 'Amelia', 'Harper', 'Evelyn']
        last_names = ['Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Taylor', 'Anderson']

        students = []
        for i in range(1, 31):
            gender = 'Male' if i % 2 == 0 else 'Female'
            fn = random.choice(first_names_m if gender == 'Male' else first_names_f)
            ln = random.choice(last_names)
            s_id = f'STU{i:04d}'
            email = f'student{i:03d}@school.edu'
            user = User(username=f'student{i:03d}', email=email, role='student')
            user.set_password('student123')
            db.session.add(user)
            db.session.flush()
            cls = classes[(i - 1) % len(classes)]
            parent = parents[(i - 1) % len(parents)]
            s = Student(
                user_id=user.id,
                student_id=s_id,
                first_name=fn,
                last_name=ln,
                date_of_birth=date(2007 - (i % 4), (i % 12) + 1, (i % 28) + 1),
                gender=gender,
                blood_group=random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'O-']),
                address=f'{100+i} Oak Street, Springfield',
                city='Springfield',
                phone=f'+1-555-{3000+i}',
                email=email,
                class_id=cls.id,
                parent_id=parent.id,
                enrollment_date=date(2024, 8, 15),
                admission_number=f'ADM{2024}{i:03d}',
                nationality='American',
                status='active',
            )
            db.session.add(s)
            students.append(s)
        db.session.flush()

        print("Seeding Attendance…")
        att_dates = [date(2024, m, d) for m in [9, 10, 11] for d in range(1, 20) if date(2024, m, d).weekday() < 5]
        for student in students[:15]:
            for att_date in att_dates[:20]:
                status = random.choices(['present', 'absent', 'late'], weights=[80, 10, 10])[0]
                subj = subjects[0] if subjects else None
                try:
                    a = Attendance(
                        student_id=student.id,
                        subject_id=subj.id if subj else None,
                        class_id=student.class_id,
                        date=att_date,
                        status=status,
                        marked_by=admin_user.id,
                    )
                    db.session.add(a)
                    db.session.flush()
                except Exception:
                    db.session.rollback()

        print("Seeding Exams…")
        exams = []
        exam_data = [
            ('Mid-Term Mathematics', 'midterm', subjects[0], classes[0], date(2024, 10, 15), 100, 40),
            ('Physics Quiz 1', 'quiz', subjects[1], classes[0], date(2024, 9, 20), 50, 20),
            ('English Assignment', 'assignment', subjects[2], classes[0], date(2024, 10, 5), 30, 12),
            ('Final Mathematics', 'final', subjects[0], classes[0], date(2024, 12, 10), 100, 40),
            ('CS Mid-Term', 'midterm', subjects[4], classes[0], date(2024, 10, 20), 100, 40),
        ]
        for name, etype, subj, cls, edate, total, passing in exam_data:
            exam = Exam(
                name=name,
                exam_type=etype,
                subject_id=subj.id,
                class_id=cls.id,
                date=edate,
                duration_minutes=60,
                total_marks=total,
                passing_marks=passing,
                teacher_id=subj.teacher_id,
                academic_year='2024-2025',
                status='completed',
                created_by=admin_user.id,
            )
            db.session.add(exam)
            exams.append(exam)
        db.session.flush()

        print("Seeding Exam Results…")
        class0_students = [s for s in students if s.class_id == classes[0].id]
        for exam in exams:
            for student in class0_students:
                marks = random.uniform(exam.passing_marks * 0.8, exam.total_marks)
                is_absent = random.random() < 0.05
                grade, gp = ExamResult.calculate_grade(marks, exam.total_marks) if not is_absent else ('F', 0)
                r = ExamResult(
                    exam_id=exam.id,
                    student_id=student.id,
                    marks_obtained=round(marks, 1) if not is_absent else None,
                    grade=grade if not is_absent else None,
                    grade_points=gp if not is_absent else None,
                    is_absent=is_absent,
                    entered_by=admin_user.id,
                )
                db.session.add(r)
        db.session.flush()

        print("Seeding Fee Structures…")
        fee_structs = []
        for cls in classes:
            fs = FeeStructure(
                name=f'Monthly Tuition — {cls.full_name}',
                class_id=cls.id,
                fee_type='tuition',
                amount=500,
                frequency='monthly',
                due_date=date(2024, 9, 10),
                academic_year='2024-2025',
            )
            db.session.add(fs)
            fee_structs.append(fs)

        exam_fee = FeeStructure(name='Annual Exam Fee', fee_type='exam', amount=150,
                                frequency='yearly', academic_year='2024-2025')
        activity_fee = FeeStructure(name='Activity Fund', fee_type='activity', amount=50,
                                    frequency='yearly', academic_year='2024-2025')
        db.session.add(exam_fee)
        db.session.add(activity_fee)
        db.session.flush()

        print("Seeding Fee Payments…")
        months = ['September 2024', 'October 2024', 'November 2024']
        for student in students[:20]:
            fs = fee_structs[(students.index(student)) % len(fee_structs)]
            for month in months:
                paid = random.random() > 0.2
                rcp_no = 'RCP-' + ''.join(random.choices(string.digits, k=8))
                p = FeePayment(
                    receipt_number=rcp_no,
                    student_id=student.id,
                    fee_structure_id=fs.id,
                    amount_due=500,
                    amount_paid=500 if paid else 0,
                    discount=0,
                    fine=0 if paid else 25,
                    payment_date=date(2024, random.randint(9, 11), random.randint(1, 28)) if paid else None,
                    payment_method=random.choice(['cash', 'bank_transfer', 'online', 'card']) if paid else None,
                    status='paid' if paid else 'pending',
                    month=month,
                    academic_year='2024-2025',
                    collected_by=admin_user.id,
                )
                db.session.add(p)
        db.session.flush()

        print("Seeding Certificates…")
        import string as str_module
        for i, student in enumerate(students[:10]):
            cert_no = 'CERT-' + ''.join(random.choices(str_module.ascii_uppercase + string.digits, k=8))
            cert = Certificate(
                certificate_number=cert_no,
                student_id=student.id,
                certificate_type=random.choice(['completion', 'merit', 'participation', 'achievement']),
                title=f'Certificate of {random.choice(["Academic Excellence", "Participation", "Merit", "Achievement"])}',
                description=f'This certifies that {student.full_name} has successfully demonstrated outstanding performance.',
                issue_date=date(2024, 12, 15),
                issued_by=admin_user.id,
                academic_year='2024-2025',
                status='issued',
            )
            db.session.add(cert)
        db.session.flush()

        print("Seeding Employees (HR)…")
        emp_data = [
            ('Alice', 'Cooper', 'HR001', 'HR Manager', depts[6].id, 7000),
            ('Bob', 'Turner', 'HR002', 'Finance Officer', depts[7].id, 6500),
            ('Carol', 'Reed', 'HR003', 'Administrative Assistant', depts[6].id, 4500),
            ('Dan', 'Morris', 'HR004', 'IT Technician', depts[4].id, 5000),
            ('Eve', 'Patterson', 'HR005', 'Librarian', depts[6].id, 4000),
        ]
        employees = []
        for fn, ln, emp_id, desig, dept_id, sal in emp_data:
            email = f'{emp_id.lower()}@school.edu'
            user = User(username=emp_id.lower(), email=email, role='hr')
            user.set_password('hr123')
            db.session.add(user)
            db.session.flush()
            emp = Employee(
                user_id=user.id,
                employee_id=emp_id,
                first_name=fn,
                last_name=ln,
                email=email,
                phone=f'+1-555-{4000 + len(employees)}',
                department_id=dept_id,
                designation=desig,
                employment_type='full-time',
                joining_date=date(2021, random.randint(1, 12), 1),
                basic_salary=sal,
                status='active',
            )
            db.session.add(emp)
            employees.append(emp)
        db.session.flush()

        print("Seeding Leave Requests…")
        leave_types = ['annual', 'sick', 'emergency', 'study']
        for emp in employees[:3]:
            lr = LeaveRequest(
                employee_id=emp.id,
                leave_type=random.choice(leave_types),
                start_date=date(2024, 11, 10),
                end_date=date(2024, 11, 12),
                days_requested=3,
                reason='Personal reasons requiring time off.',
                status=random.choice(['pending', 'approved', 'rejected']),
                created_at=datetime(2024, 11, 1),
            )
            db.session.add(lr)
        db.session.flush()

        print("Seeding Payroll…")
        for emp in employees:
            for month in [9, 10, 11]:
                p = Payroll(
                    employee_id=emp.id,
                    month=month,
                    year=2024,
                    basic_salary=emp.basic_salary,
                    house_allowance=emp.basic_salary * 0.2,
                    transport_allowance=emp.basic_salary * 0.1,
                    medical_allowance=emp.basic_salary * 0.05,
                    tax_deduction=emp.basic_salary * 0.1,
                    pension_deduction=emp.basic_salary * 0.05,
                    payment_date=date(2024, month, 28),
                    payment_method='bank_transfer',
                    status='paid',
                    processed_by=admin_user.id,
                )
                p.calculate()
                db.session.add(p)
        db.session.flush()

        print("Seeding Announcements…")
        ann_data = [
            ('Welcome to Academic Year 2024-2025', 'We are pleased to welcome all students and staff to the new academic year. Please review the updated timetables and guidelines.', 'all', 'normal'),
            ('Mid-Term Exams Schedule Released', 'The mid-term examination schedule is now available. Please check your student portal for details.', 'students', 'high'),
            ('Staff Meeting — November', 'All teaching staff are requested to attend the monthly staff meeting on November 5th at 3:00 PM in the main hall.', 'teachers', 'normal'),
            ('Fee Payment Reminder', 'This is a reminder that November fee payments are due by the 10th. Late payments will attract a fine.', 'parents', 'high'),
            ('Annual Sports Day', 'The Annual Sports Day is scheduled for December 5th. All students are encouraged to participate.', 'all', 'normal'),
        ]
        for title, content, audience, priority in ann_data:
            ann = Announcement(
                title=title,
                content=content,
                target_audience=audience,
                priority=priority,
                is_published=True,
                created_by=admin_user.id,
            )
            db.session.add(ann)

        db.session.commit()

        print("\n✅ Seeding complete!")
        print("\n─── Demo Login Credentials ───")
        print("Admin:    admin / admin123")
        print("Student:  student001 / student123")
        print("Teacher:  teacher001 / teacher123")
        print("Parent:   parent001 / parent123")
        print("HR:       hr001 / hr123")
        print("\nRun: python app.py")
        print("Open: http://localhost:5000")


if __name__ == '__main__':
    seed()
