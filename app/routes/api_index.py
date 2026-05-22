import json
import time
from flask import Blueprint, Response, current_app, jsonify, request
from flask_login import login_required, current_user
from ..config import load_config
from ..indexer import get_status, reset_index, start_indexing
from ..routes.api_folders import invalidate_folder_cache

bp = Blueprint("api_index", __name__, url_prefix="/api/index")


@bp.route("/start", methods=["POST"])
@login_required
def start():
    cfg = load_config()
    # Use user's email_folder if set, else global root_path
    root_path = current_user.email_folder or cfg.root_path
    if not root_path:
        return jsonify({"error": "root_path not configured"}), 400
    result = start_indexing(current_user.id, root_path, current_app._get_current_object())
    invalidate_folder_cache(current_user.id)
    return jsonify({"status": result})


@bp.route("/status", methods=["GET"])
@login_required
def status():
    return jsonify(get_status(current_user.id))


@bp.route("/progress")
@login_required
def progress():
    """Server-Sent Events stream for indexing progress."""
    user_id = current_user.id  # capture before request context is torn down

    def generate():
        max_seconds = 3600  # 1 hour max stream
        start = time.time()
        while time.time() - start < max_seconds:
            state = get_status(user_id)
            data = json.dumps({
                "status": state.get("status", "idle"),
                "total": state.get("total_files", 0),
                "done": state.get("done_files", 0),
                "skipped": state.get("skipped", 0),
                "percent": round(
                    state["done_files"] / state["total_files"] * 100, 1
                ) if state.get("total_files") else 0,
            })
            yield f"data: {data}\n\n"
            if state.get("status") in ("done", "error", "idle"):
                invalidate_folder_cache(user_id)
                break
            time.sleep(1)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@bp.route("/reset", methods=["DELETE"])
@login_required
def reset():
    state = get_status(current_user.id)
    if state.get("status") == "running":
        return jsonify({"error": "Cannot reset while indexing is running"}), 409
    reset_index(current_user.id)
    invalidate_folder_cache(current_user.id)
    return jsonify({"ok": True})
