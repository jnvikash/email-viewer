import json
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..db import get_db
from ..msg_parser import get_msg_body, list_attachments
from ..sanitizer import sanitize_html, text_to_html

bp = Blueprint("api_emails", __name__, url_prefix="/api/emails")

VALID_SORTS = {
    "date": "date_sent",
    "-date": "date_sent DESC",
    "sender": "sender_name",
    "-sender": "sender_name DESC",
    "subject": "subject",
    "-subject": "subject DESC",
}


@bp.route("", methods=["GET"])
@login_required
def list_emails():
    folder = request.args.get("folder", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(200, max(1, int(request.args.get("per_page", 50))))
    sort = request.args.get("sort", "-date")
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    sender = request.args.get("sender", "").strip()

    order = VALID_SORTS.get(sort, "date_sent DESC")
    offset = (page - 1) * per_page

    conditions = ["user_id = ?"]
    params: list = [current_user.id]

    if folder and folder != "__all__":
        conditions.append("(folder_path = ? OR folder_path LIKE ?)")
        params += [folder, folder + "/%"]

    if date_from:
        conditions.append("date_sent >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date_sent <= ?")
        params.append(date_to + "T23:59:59")
    if sender:
        conditions.append("(sender_name LIKE ? OR sender_email LIKE ?)")
        params += [f"%{sender}%", f"%{sender}%"]

    where = "WHERE " + " AND ".join(conditions)

    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM emails {where}", params).fetchone()[0]
    rows = db.execute(
        f"SELECT id, subject, sender_name, sender_email, date_sent, body_preview, attachment_count, has_html_body, importance "
        f"FROM emails {where} ORDER BY {order} NULLS LAST LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "emails": [dict(r) for r in rows],
    })


@bp.route("/index-status", methods=["GET"])
@login_required
def index_status():
    """Get indexing status with email counts."""
    from ..indexer import get_status

    db = get_db()
    indexed_count = db.execute(
        "SELECT COUNT(*) FROM emails WHERE user_id=?",
        (current_user.id,)
    ).fetchone()[0]

    indexer_status = get_status(current_user.id)

    return jsonify({
        "indexed_count": indexed_count,
        "total_files": indexer_status.get("total_files", 0),
        "indexing": indexer_status.get("status") == "running",
        "status": indexer_status.get("status", "idle"),
        "percent": round(
            indexer_status.get("done_files", 0) / indexer_status.get("total_files", 1) * 100, 1
        ) if indexer_status.get("total_files") else 0
    })


@bp.route("/<int:email_id>", methods=["GET"])
@login_required
def get_email(email_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM emails WHERE id=? AND user_id=?", (email_id, current_user.id)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404

    email = dict(row)
    file_path = email["file_path"]

    # Parse recipients from JSON
    try:
        email["recipients"] = json.loads(email.get("recipients") or "[]")
    except Exception:
        email["recipients"] = []

    # Fetch attachments from DB
    atts = db.execute(
        "SELECT id, filename, mime_type, size_bytes, attach_index FROM attachments WHERE email_id=? ORDER BY attach_index",
        (email_id,),
    ).fetchall()
    attachments = [dict(a) for a in atts]
    email["attachments"] = attachments

    # Get body
    html_body, text_body = get_msg_body(file_path)
    if html_body:
        email["body_html"] = sanitize_html(html_body, email_id=email_id, attachments=attachments)
        email["body_text"] = text_body
    else:
        email["body_html"] = ""
        email["body_text"] = text_body

    # Remove raw file_path from response (security)
    email.pop("file_path", None)

    return jsonify(email)
