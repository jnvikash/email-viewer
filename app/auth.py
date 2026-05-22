from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, timezone
from .db import get_db
import secrets

bp = Blueprint("auth", __name__)
login_manager = LoginManager()


class User(UserMixin):
    """User object for Flask-Login."""
    def __init__(self, user_id, username, is_admin=False, email_folder=None):
        self.id = user_id
        self.username = username
        self.is_admin = is_admin
        self.email_folder = email_folder


@login_manager.user_loader
def load_user(user_id):
    """Load user from database."""
    try:
        db = get_db()
        row = db.execute("SELECT id, username, is_admin, email_folder FROM users WHERE id=? AND is_active=1", (int(user_id),)).fetchone()
        if row:
            return User(row["id"], row["username"], row["is_admin"], row["email_folder"])
    except Exception:
        pass
    return None


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT id, username, password_hash, is_admin, email_folder FROM users WHERE username=? AND is_active=1",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            user_obj = User(user["id"], user["username"], user["is_admin"], user["email_folder"])
            login_user(user_obj, remember=True)
            return redirect(url_for("main.app_shell"))

        flash("Invalid username or password.", "danger")

    # Check if any users exist (first run setup)
    db = get_db()
    user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    first_run = user_count == 0

    return render_template("login.html", first_run=first_run)


@bp.route("/register", methods=["GET", "POST"])
def register():
    """First run: create admin user."""
    db = get_db()
    user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    if user_count > 0:
        flash("Registration is closed. Please log in.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email_folder = request.form.get("email_folder", "").strip()

        if not username or len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return redirect(url_for("auth.register"))

        if not password or len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        if db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        try:
            now = datetime.now(timezone.utc).isoformat()
            db.execute(
                """INSERT INTO users (username, password_hash, email_folder, is_admin, created_at, updated_at)
                   VALUES (?, ?, ?, 1, ?, ?)""",
                (username, generate_password_hash(password), email_folder or None, now, now)
            )
            db.commit()

            # Auto-login
            user = db.execute(
                "SELECT id, username, is_admin, email_folder FROM users WHERE username=?",
                (username,)
            ).fetchone()
            user_obj = User(user["id"], user["username"], user["is_admin"], user["email_folder"])
            login_user(user_obj, remember=True)

            flash("Admin account created successfully!", "success")
            return redirect(url_for("main.app_shell"))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")

    return render_template("register.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

