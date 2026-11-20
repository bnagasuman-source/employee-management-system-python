from flask import Flask, jsonify, redirect, request, url_for

from api import api_bp
from auth import auth_bp
from config import Config, ensure_database
from models import Admin, Department, db, login_manager

DEFAULT_DEPARTMENTS = ["Engineering", "Human Resources", "Finance", "Marketing", "Sales"]


def seed_data(app):
    """Create the default admin and departments on first run."""
    username = app.config["ADMIN_USERNAME"]
    if not Admin.query.filter_by(username=username).first():
        admin = Admin(username=username)
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
    if Department.query.count() == 0:
        db.session.add_all(Department(name=n) for n in DEFAULT_DEPARTMENTS)
    db.session.commit()


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    ensure_database(app.config["SQLALCHEMY_DATABASE_URI"])
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(message="Authentication required"), 401
        return redirect(url_for("auth.login"))

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        seed_data(app)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
