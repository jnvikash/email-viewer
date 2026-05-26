import time
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from ..db import get_db

bp = Blueprint("api_folders", __name__, url_prefix="/api/folders")

_cache: dict = {"tree": {}}
_CACHE_TTL = 60  # seconds


def _build_tree(rows: list) -> list:
    """Build a nested tree from flat (folder_path, count) rows."""
    root_children = []
    nodes: dict[str, dict] = {}

    # Add "All Mail" virtual root
    total = sum(r["cnt"] for r in rows)
    all_mail = {"name": "All Mail", "path": "__all__", "children": [], "email_count": total}

    for row in rows:
        path = row["folder_path"]
        count = row["cnt"]
        parts = [p for p in path.replace("\\", "/").split("/") if p and p != "."]

        parent_list = root_children
        built_path = ""
        for i, part in enumerate(parts):
            built_path = "/".join(parts[: i + 1])
            if built_path not in nodes:
                node = {"name": part, "path": built_path, "children": [], "email_count": 0}
                nodes[built_path] = node
                parent_list.append(node)
            node = nodes[built_path]
            if i == len(parts) - 1:
                node["email_count"] += count
            parent_list = node["children"]

    return [all_mail] + root_children


@bp.route("", methods=["GET"])
@login_required
def get_folders():
    global _cache
    now = time.time()
    cache_key = f"user_{current_user.id}"

    # Don't cache if indexing is in progress (refresh live)
    from ..indexer import get_status
    status = get_status(current_user.id)
    is_indexing = status.get("status") == "running"

    if not is_indexing and cache_key in _cache and (now - _cache[cache_key]["ts"]) < _CACHE_TTL:
        return jsonify(_cache[cache_key]["tree"])

    db = get_db()
    rows = db.execute(
        "SELECT folder_path, COUNT(*) as cnt FROM emails WHERE user_id=? GROUP BY folder_path ORDER BY folder_path",
        (current_user.id,)
    ).fetchall()

    tree = _build_tree(rows)

    # Add indexing status to response
    if is_indexing:
        total = status.get("total_files", 0)
        done = status.get("done_files", 0)
        response = {
            "folders": tree,
            "indexing": {
                "status": "running",
                "done": done,
                "total": total,
                "percent": round(done / total * 100, 1) if total > 0 else 0
            }
        }
    else:
        response = {"folders": tree, "indexing": None}

    if not is_indexing:
        _cache[cache_key] = {"tree": response, "ts": now}

    return jsonify(response)


def invalidate_folder_cache(user_id: int = None):
    global _cache
    if user_id is None:
        _cache = {"tree": {}}
    else:
        cache_key = f"user_{user_id}"
        if cache_key in _cache:
            del _cache[cache_key]
