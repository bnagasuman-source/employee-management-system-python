# Employee Management System (Python)

A full-stack web application to manage employee data, built with **Python, Flask, MySQL, HTML, CSS and JavaScript**.

## Features
- Secure admin login and authentication (Flask-Login, hashed passwords, session based)
- Add, update, delete and search employee records
- Department management (add / delete, protected while employees still belong to it)
- Salary management with a payroll total and average salary dashboard
- REST APIs integrated with a MySQL database using SQLAlchemy
- Server-side validation with clear error messages

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask, Flask-SQLAlchemy, Flask-Login |
| Database | MySQL 8 (PyMySQL driver) |
| Frontend | HTML, CSS, JavaScript (fetch API) |

## Project Structure
```
app.py            App factory, seeding (admin + departments), entry point
config.py         Environment-based configuration, auto-creates the MySQL database
models.py         Admin, Department, Employee models
auth.py           Login / logout / dashboard routes
api.py            REST API for employees and departments
templates/        login.html, index.html
static/           css/style.css, js/app.js
tests/            Unit tests (run on in-memory SQLite)
```

## Getting Started
1. Install Python 3.10+ and MySQL 8, and make sure MySQL is running.
2. Clone the repo and create a virtual environment:
   ```bash
   git clone https://github.com/<your-username>/employee-management-system-python.git
   cd employee-management-system-python
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # Mac / Linux
   pip install -r requirements.txt
   ```
3. Configure the database: copy `.env.example` to `.env` and set `DB_PASSWORD` (and `SECRET_KEY`).
4. Run:
   ```bash
   python app.py
   ```
5. Open http://127.0.0.1:5000 and log in with the default admin (`admin` / `admin123`).
   Tables and the `ems_db` database are created automatically on first run.

## REST API
All endpoints require a logged-in session.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | List employees (`?search=` filters by name, email, department) |
| GET | `/api/employees/<id>` | Get one employee |
| GET | `/api/employees/stats` | Headcount, payroll, average salary |
| POST | `/api/employees` | Add employee |
| PUT | `/api/employees/<id>` | Update employee |
| DELETE | `/api/employees/<id>` | Delete employee |
| GET | `/api/departments` | List departments |
| POST | `/api/departments` | Add department |
| DELETE | `/api/departments/<id>` | Delete department |

## Tests
```bash
python -m unittest discover -s tests
```

## Notes
- CSRF protection is not enabled to keep the demo simple. Add Flask-WTF CSRF before production use.
- Change the default admin password and `SECRET_KEY` before deploying.
