import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from ..db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.app_shell"))
        return f(*args, **kwargs)
    return decorated_function


@bp.route("/")
@login_required
@admin_required
def dashboard():
    db = get_db()

    total_users = db.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]
    total_emails = db.execute("SELECT COUNT(*) FROM emails").fetchone()[0]

    # Per-user email counts and index state
    users = db.execute("""
        SELECT u.id, u.username, u.email_folder, u.is_admin, u.created_at, u.is_active,
               COUNT(e.id) AS email_count,
               COALESCE(ix.status, 'idle') AS index_status,
               COALESCE(ix.done_files, 0) AS done_files,
               COALESCE(ix.total_files, 0) AS total_files,
               ix.finished_at
        FROM users u
        LEFT JOIN emails e ON e.user_id = u.id
        LEFT JOIN index_state ix ON ix.user_id = u.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """).fetchall()

    return render_template("admin/dashboard.html",
                           total_users=total_users,
                           total_emails=total_emails,
                           users=[dict(u) for u in users])


@bp.route("/users")
@login_required
@admin_required
def manage_users():
    db = get_db()
    users = db.execute(
        "SELECT id, username, email_folder, is_admin, created_at, is_active FROM users ORDER BY created_at DESC"
    ).fetchall()
    return render_template("admin/manage_users.html", users=[dict(u) for u in users])


# ── User CRUD APIs ────────────────────────────────────────────────────────────

@bp.route("/api/users", methods=["GET"])
@login_required
@admin_required
def get_users():
    db = get_db()
    users = db.execute("""
        SELECT u.id, u.username, u.email_folder, u.is_admin, u.created_at, u.is_active,
               COUNT(e.id) AS email_count,
               COALESCE(ix.status, 'idle') AS index_status,
               COALESCE(ix.done_files, 0) AS done_files,
               COALESCE(ix.total_files, 0) AS total_files,
               ix.finished_at
        FROM users u
        LEFT JOIN emails e ON e.user_id = u.id
        LEFT JOIN index_state ix ON ix.user_id = u.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """).fetchall()
    return jsonify([dict(u) for u in users])


@bp.route("/api/users", methods=["POST"])
@login_required
@admin_required
def create_user():
    data = request.get_json(force=True, silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email_folder = data.get("email_folder", "").strip()
    is_admin = bool(data.get("is_admin", False))

    if not username or len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    if db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
        return jsonify({"error": "Username already exists"}), 400

    try:
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "INSERT INTO users (username, password_hash, email_folder, is_admin, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, generate_password_hash(password), email_folder or None, 1 if is_admin else 0, now, now)
        )
        db.commit()

        user_id = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
        try:
            db.execute("INSERT INTO index_state (user_id, status) VALUES (?, 'idle')", (user_id,))
            db.commit()
        except Exception:
            pass

        return jsonify({"ok": True, "username": username}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required
@admin_required
def update_user(user_id):
    data = request.get_json(force=True, silent=True) or {}

    db = get_db()
    if not db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        return jsonify({"error": "User not found"}), 404

    email_folder = data.get("email_folder", "").strip()
    is_admin = bool(data.get("is_admin", False))

    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE users SET email_folder=?, is_admin=?, updated_at=? WHERE id=?",
        (email_folder or None, 1 if is_admin else 0, now, user_id)
    )
    db.commit()
    return jsonify({"ok": True})


@bp.route("/api/users/<int:user_id>/password", methods=["POST"])
@login_required
@admin_required
def change_user_password(user_id):
    data = request.get_json(force=True, silent=True) or {}
    password = data.get("password", "").strip()
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    if not db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        return jsonify({"error": "User not found"}), 404

    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE users SET password_hash=?, updated_at=? WHERE id=?",
        (generate_password_hash(password), now, user_id)
    )
    db.commit()
    return jsonify({"ok": True})


@bp.route("/api/users/<int:user_id>/deactivate", methods=["POST"])
@login_required
@admin_required
def deactivate_user(user_id):
    if user_id == current_user.id:
        return jsonify({"error": "Cannot deactivate yourself"}), 400

    db = get_db()
    if not db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        return jsonify({"error": "User not found"}), 404

    now = datetime.now(timezone.utc).isoformat()
    db.execute("UPDATE users SET is_active=0, updated_at=? WHERE id=?", (now, user_id))
    db.commit()
    return jsonify({"ok": True})


@bp.route("/api/users/<int:user_id>/activate", methods=["POST"])
@login_required
@admin_required
def activate_user(user_id):
    db = get_db()
    if not db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        return jsonify({"error": "User not found"}), 404

    now = datetime.now(timezone.utc).isoformat()
    db.execute("UPDATE users SET is_active=1, updated_at=? WHERE id=?", (now, user_id))
    db.commit()
    return jsonify({"ok": True})


# ── Index management ──────────────────────────────────────────────────────────

@bp.route("/api/users/<int:user_id>/status", methods=["GET"])
@login_required
@admin_required
def user_index_status(user_id):
    from ..indexer import get_status
    return jsonify(get_status(user_id))


@bp.route("/api/users/<int:user_id>/reindex", methods=["POST"])
@login_required
@admin_required
def reindex_user(user_id):
    from ..indexer import start_indexing
    from ..routes.api_folders import invalidate_folder_cache

    db = get_db()
    user = db.execute("SELECT id, email_folder FROM users WHERE id=? AND is_active=1", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not user["email_folder"]:
        return jsonify({"error": "User has no email folder configured"}), 400

    result = start_indexing(user_id, user["email_folder"], current_app._get_current_object())
    invalidate_folder_cache(user_id)
    return jsonify({"status": result})


# ── Filesystem browser ────────────────────────────────────────────────────────

@bp.route("/api/browse")
@login_required
@admin_required
def browse_folder():
    """Browse server filesystem directories for folder path selection."""
    raw = request.args.get("path", "").strip()

    # Default to home or root
    if not raw:
        raw = os.path.expanduser("~")

    try:
        abs_path = os.path.realpath(raw)
    except Exception:
        abs_path = os.path.expanduser("~")

    # Walk up until we find an existing directory
    while abs_path and not os.path.isdir(abs_path):
        parent = os.path.dirname(abs_path)
        if parent == abs_path:
            abs_path = "/"
            break
        abs_path = parent

    try:
        entries = []
        with os.scandir(abs_path) as it:
            for entry in sorted(it, key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower())):
                if entry.name.startswith("."):
                    continue
                try:
                    is_dir = entry.is_dir(follow_symlinks=True)
                except OSError:
                    is_dir = False
                entries.append({
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": is_dir,
                })

        parent = os.path.dirname(abs_path) if abs_path != os.path.dirname(abs_path) else None

        return jsonify({
            "current": abs_path,
            "parent": parent,
            "entries": entries,
            "error": None,
        })
    except PermissionError:
        parent = os.path.dirname(abs_path)
        return jsonify({
            "current": abs_path,
            "parent": parent if parent != abs_path else None,
            "entries": [],
            "error": "Permission denied",
        })
    except Exception as e:
        return jsonify({"error": str(e), "current": abs_path, "parent": None, "entries": []}), 500
