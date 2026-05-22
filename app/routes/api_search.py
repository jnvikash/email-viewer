import re
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..db import get_db

bp = Blueprint("api_search", __name__, url_prefix="/api/search")

_UNSAFE_FTS = re.compile(r'["\'\(\)\*\+]')


def _safe_fts_query(q: str) -> str:
    """Escape user input for FTS5 MATCH. Wraps in quotes if no special operators."""
    q = q.strip()
    upper = q.upper()
    has_operators = any(op in upper for op in (" AND ", " OR ", " NOT ")) or "*" in q
    if has_operators:
        return q
    # Escape any bare quotes and wrap as phrase
    q_escaped = q.replace('"', '""')
    return f'"{q_escaped}"'


@bp.route("", methods=["GET"])
@login_required
def search():
    q = request.args.get("q", "").strip()
    folder = request.args.get("folder", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(200, max(1, int(request.args.get("per_page", 50))))
    offset = (page - 1) * per_page

    if not q:
        return jsonify({"total": 0, "page": 1, "per_page": per_page, "query": q, "emails": []})

    db = get_db()

    folder_filter = ""
    folder_params: list = []
    if folder and folder != "__all__":
        folder_filter = "AND (e.folder_path = ? OR e.folder_path LIKE ?)"
        folder_params = [folder, folder + "/%"]

    try:
        fts_q = _safe_fts_query(q)
        count_row = db.execute(
            f"SELECT COUNT(*) FROM emails_fts f JOIN emails e ON f.rowid = e.id WHERE e.user_id = ? AND emails_fts MATCH ? {folder_filter}",
            [current_user.id, fts_q] + folder_params,
        ).fetchone()
        total = count_row[0] if count_row else 0

        rows = db.execute(
            f"""SELECT e.id, e.subject, e.sender_name, e.sender_email, e.date_sent,
                       e.body_preview, e.attachment_count, e.has_html_body, e.importance,
                       snippet(emails_fts, 3, '<mark>', '</mark>', '...', 32) AS snippet
                FROM emails_fts f
                JOIN emails e ON f.rowid = e.id
                WHERE e.user_id = ? AND emails_fts MATCH ?
                {folder_filter}
                ORDER BY rank
                LIMIT ? OFFSET ?""",
            [current_user.id, fts_q] + folder_params + [per_page, offset],
        ).fetchall()

    except Exception:
        # FTS syntax error fallback to LIKE search
        like_q = f"%{q}%"
        folder_cond = ""
        like_params: list = [current_user.id, like_q, like_q, like_q]
        if folder and folder != "__all__":
            folder_cond = "AND (folder_path = ? OR folder_path LIKE ?)"
            like_params += [folder, folder + "/%"]

        count_row = db.execute(
            f"SELECT COUNT(*) FROM emails WHERE user_id = ? AND (subject LIKE ? OR sender_name LIKE ? OR body_preview LIKE ?) {folder_cond}",
            like_params,
        ).fetchone()
        total = count_row[0] if count_row else 0

        rows = db.execute(
            f"""SELECT id, subject, sender_name, sender_email, date_sent,
                       body_preview, attachment_count, has_html_body, importance,
                       body_preview AS snippet
                FROM emails
                WHERE user_id = ? AND (subject LIKE ? OR sender_name LIKE ? OR body_preview LIKE ?)
                {folder_cond}
                ORDER BY date_sent DESC NULLS LAST
                LIMIT ? OFFSET ?""",
            like_params + [per_page, offset],
        ).fetchall()

    results = [dict(r) for r in rows]
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "query": q,
        "emails": results,
    })
