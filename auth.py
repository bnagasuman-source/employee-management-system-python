from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models import Admin

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for("auth.index"))
        error = "Invalid username or password"

    return render_template("login.html", error=error,
                           logged_out=request.args.get("logout") == "1")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return ("", 204)


@auth_bp.route("/")
@login_required
def index():
    return render_template("index.html")
