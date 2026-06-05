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


def _build_extra_conditions(request_args):
    """Return (sql_fragment, params) for structured filter fields shared by search and list."""
    conds = []
    params = []
    date_from = request_args.get("date_from", "").strip()
    date_to = request_args.get("date_to", "").strip()
    from_email = request_args.get("from_email", "").strip()
    to_email = request_args.get("to_email", "").strip()
    subject_q = request_args.get("subject", "").strip()
    has_attachment = request_args.get("has_attachment", "").strip()

    if date_from:
        conds.append("e.date_sent >= ?")
        params.append(date_from)
    if date_to:
        conds.append("e.date_sent <= ?")
        params.append(date_to + "T23:59:59")
    if from_email:
        conds.append("e.sender_email LIKE ?")
        params.append(f"%{from_email}%")
    if to_email:
        conds.append("e.recipients LIKE ?")
        params.append(f"%{to_email}%")
    if subject_q:
        conds.append("e.subject LIKE ?")
        params.append(f"%{subject_q}%")
    if has_attachment == "1":
        conds.append("e.attachment_count > 0")

    fragment = (" AND " + " AND ".join(conds)) if conds else ""
    return fragment, params


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

    extra_cond, extra_params = _build_extra_conditions(request.args)

    try:
        fts_q = _safe_fts_query(q)
        base_params = [current_user.id, fts_q] + folder_params + extra_params

        count_row = db.execute(
            f"SELECT COUNT(*) FROM emails_fts f JOIN emails e ON f.rowid = e.id "
            f"WHERE e.user_id = ? AND emails_fts MATCH ? {folder_filter}{extra_cond}",
            base_params,
        ).fetchone()
        total = count_row[0] if count_row else 0

        rows = db.execute(
            f"""SELECT e.id, e.subject, e.sender_name, e.sender_email, e.date_sent,
                       e.body_preview, e.attachment_count, e.has_html_body, e.importance,
                       snippet(emails_fts, 3, '<mark>', '</mark>', '...', 32) AS snippet
                FROM emails_fts f
                JOIN emails e ON f.rowid = e.id
                WHERE e.user_id = ? AND emails_fts MATCH ?
                {folder_filter}{extra_cond}
                ORDER BY rank
                LIMIT ? OFFSET ?""",
            base_params + [per_page, offset],
        ).fetchall()

    except Exception:
        # FTS syntax error — fallback to LIKE search
        like_q = f"%{q}%"
        folder_cond = ""
        like_params: list = [current_user.id, like_q, like_q, like_q]
        if folder and folder != "__all__":
            folder_cond = "AND (folder_path = ? OR folder_path LIKE ?)"
            like_params += [folder, folder + "/%"]

        # rebuild extra_cond without table alias for the plain emails table fallback
        extra_cond_plain = extra_cond.replace("e.", "")
        like_params_full = like_params + extra_params

        count_row = db.execute(
            f"SELECT COUNT(*) FROM emails WHERE user_id = ? "
            f"AND (subject LIKE ? OR sender_name LIKE ? OR body_preview LIKE ?) "
            f"{folder_cond}{extra_cond_plain}",
            like_params_full,
        ).fetchone()
        total = count_row[0] if count_row else 0

        rows = db.execute(
            f"""SELECT id, subject, sender_name, sender_email, date_sent,
                       body_preview, attachment_count, has_html_body, importance,
                       body_preview AS snippet
                FROM emails
                WHERE user_id = ? AND (subject LIKE ? OR sender_name LIKE ? OR body_preview LIKE ?)
                {folder_cond}{extra_cond_plain}
                ORDER BY date_sent DESC NULLS LAST
                LIMIT ? OFFSET ?""",
            like_params_full + [per_page, offset],
        ).fetchall()

    results = [dict(r) for r in rows]
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "query": q,
        "emails": results,
    })
