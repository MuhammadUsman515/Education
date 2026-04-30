# EduManage Pro — Comprehensive Education Management System

A full-featured, premium education management system built with Flask, supporting five role-based portals.

## Features

- **5 Portals**: Admin, Student, Teacher, Parent, HR
- **Student Management**: Enrollment, profiles, attendance, grades, fees, certificates
- **Teacher Management**: Subject assignment, attendance marking, exam creation & grading
- **Exam Management**: Schedule exams, enter results, auto-calculate grades & GPA
- **Fee Management**: Fee structures, collections, receipts, CSV export
- **Certificate Management**: Issue merit, completion, and participation certificates
- **HR & Payroll**: Employee records, leave approval, automated payroll generation
- **Reports & Exports**: CSV exports for students, fees, and payroll
- **Premium UI**: Bootstrap 5, Chart.js, Font Awesome — fully responsive

## Quick Start

```bash
pip install -r requirements.txt
python seed.py       # Creates DB with sample data
python app.py        # Start server at http://localhost:5000
```

## Demo Credentials

| Role    | Username    | Password     |
|---------|-------------|--------------|
| Admin   | admin       | admin123     |
| Student | student001  | student123   |
| Teacher | teacher001  | teacher123   |
| Parent  | parent001   | parent123    |
| HR      | hr001       | hr123        |

## Tech Stack

- **Backend**: Python 3 / Flask 3
- **Database**: SQLite (via SQLAlchemy)
- **Frontend**: Bootstrap 5.3, Chart.js, Font Awesome 6, custom CSS
- **Auth**: Flask-Login (session-based, role-based access)
