import re
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from models import Department, Employee, db

api_bp = Blueprint("api", __name__, url_prefix="/api")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\- ]{7,20}$")


def error(message, status=400):
    return jsonify(message=message), status


@api_bp.before_request
def require_login():
    if not current_user.is_authenticated:
        return error("Authentication required", 401)


# ---------------------------------------------------------------- validation
def parse_employee(data):
    """Validate request JSON. Returns (clean_values, error_message)."""
    first = str(data.get("firstName") or "").strip()
    last = str(data.get("lastName") or "").strip()
    email = str(data.get("email") or "").strip()
    phone = str(data.get("phone") or "").strip()

    if not first:
        return None, "First name is required"
    if not last:
        return None, "Last name is required"
    if not email:
        return None, "Email is required"
    if not EMAIL_RE.match(email):
        return None, "Email is not valid"
    if phone and not PHONE_RE.match(phone):
        return None, "Phone number is not valid"

    try:
        salary = Decimal(str(data.get("salary")))
        if not salary.is_finite():
            raise InvalidOperation
    except (InvalidOperation, TypeError):
        return None, "Salary is required and must be a number"
    if salary < 0:
        return None, "Salary cannot be negative"

    hire_date = None
    if data.get("hireDate"):
        try:
            hire_date = date.fromisoformat(str(data["hireDate"]))
        except ValueError:
            return None, "Hire date must be in YYYY-MM-DD format"

    try:
        department_id = int(data.get("departmentId"))
    except (TypeError, ValueError):
        return None, "Department is required"
    if db.session.get(Department, department_id) is None:
        return None, "Selected department does not exist"

    return {
        "first_name": first, "last_name": last, "email": email,
        "phone": phone or None, "salary": salary, "hire_date": hire_date,
        "department_id": department_id,
    }, None


# ----------------------------------------------------------------- employees
@api_bp.get("/employees")
def list_employees():
    search = request.args.get("search", "").strip()
    query = Employee.query.outerjoin(Department)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(
            Employee.first_name.ilike(like),
            Employee.last_name.ilike(like),
            Employee.email.ilike(like),
            Department.name.ilike(like),
        ))
    employees = query.order_by(Employee.id.desc()).all()
    return jsonify([e.to_dict() for e in employees])


@api_bp.get("/employees/stats")
def stats():
    count = db.session.query(func.count(Employee.id)).scalar() or 0
    total = db.session.query(func.coalesce(func.sum(Employee.salary), 0)).scalar()
    total = Decimal(str(total))
    average = (total / count).quantize(Decimal("0.01")) if count else Decimal("0.00")
    return jsonify(
        totalEmployees=count,
        totalDepartments=db.session.query(func.count(Department.id)).scalar() or 0,
        totalPayroll=float(total),
        averageSalary=float(average),
    )


@api_bp.get("/employees/<int:emp_id>")
def get_employee(emp_id):
    employee = db.session.get(Employee, emp_id)
    if employee is None:
        return error(f"Employee not found with id {emp_id}", 404)
    return jsonify(employee.to_dict())


@api_bp.post("/employees")
def create_employee():
    values, problem = parse_employee(request.get_json(silent=True) or {})
    if problem:
        return error(problem)
    if Employee.query.filter_by(email=values["email"]).first():
        return error("An employee with this email already exists")
    employee = Employee(**values)
    db.session.add(employee)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("An employee with this email already exists")
    return jsonify(employee.to_dict()), 201


@api_bp.put("/employees/<int:emp_id>")
def update_employee(emp_id):
    employee = db.session.get(Employee, emp_id)
    if employee is None:
        return error(f"Employee not found with id {emp_id}", 404)
    values, problem = parse_employee(request.get_json(silent=True) or {})
    if problem:
        return error(problem)
    clash = Employee.query.filter(Employee.email == values["email"],
                                  Employee.id != emp_id).first()
    if clash:
        return error("Another employee already uses this email")
    for field, value in values.items():
        setattr(employee, field, value)
    db.session.commit()
    return jsonify(employee.to_dict())


@api_bp.delete("/employees/<int:emp_id>")
def delete_employee(emp_id):
    employee = db.session.get(Employee, emp_id)
    if employee is None:
        return error(f"Employee not found with id {emp_id}", 404)
    db.session.delete(employee)
    db.session.commit()
    return ("", 204)


# --------------------------------------------------------------- departments
@api_bp.get("/departments")
def list_departments():
    departments = Department.query.order_by(Department.name).all()
    return jsonify([d.to_dict() for d in departments])


@api_bp.post("/departments")
def create_department():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    if not name:
        return error("Department name is required")
    if len(name) > 100:
        return error("Department name is too long")
    if Department.query.filter(func.lower(Department.name) == name.lower()).first():
        return error("Department already exists")
    department = Department(name=name)
    db.session.add(department)
    db.session.commit()
    return jsonify(department.to_dict()), 201


@api_bp.delete("/departments/<int:dept_id>")
def delete_department(dept_id):
    department = db.session.get(Department, dept_id)
    if department is None:
        return error(f"Department not found with id {dept_id}", 404)
    if Employee.query.filter_by(department_id=dept_id).first():
        return error("Cannot delete a department that still has employees")
    db.session.delete(department)
    db.session.commit()
    return ("", 204)
