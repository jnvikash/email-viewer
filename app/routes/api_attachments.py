import io
from flask import Blueprint, Response, abort, send_file
from flask_login import login_required, current_user
from ..db import get_db
from ..msg_parser import get_attachment_bytes

bp = Blueprint("api_attachments", __name__, url_prefix="/api/attachments")


def _get_attachment(email_id: int, attach_index: int):
    db = get_db()
    email_row = db.execute("SELECT file_path FROM emails WHERE id=? AND user_id=?", (email_id, current_user.id)).fetchone()
    if not email_row:
        abort(404)

    file_path = email_row["file_path"]
    result = get_attachment_bytes(file_path, attach_index)
    if result is None:
        abort(404)

    filename, mime_type, data = result
    return filename, mime_type, data


@bp.route("/<int:email_id>/<int:attach_index>/download")
@login_required
def download(email_id: int, attach_index: int):
    filename, mime_type, data = _get_attachment(email_id, attach_index)
    return send_file(
        io.BytesIO(data),
        mimetype=mime_type,
        as_attachment=True,
        download_name=filename,
    )


@bp.route("/<int:email_id>/<int:attach_index>/preview")
@login_required
def preview(email_id: int, attach_index: int):
    filename, mime_type, data = _get_attachment(email_id, attach_index)
    return send_file(
        io.BytesIO(data),
        mimetype=mime_type,
        as_attachment=False,
        download_name=filename,
    )
