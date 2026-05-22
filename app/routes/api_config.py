from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..config import load_config, save_config

bp = Blueprint("api_config", __name__, url_prefix="/api/config")


@bp.route("", methods=["GET"])
@login_required
def get_config():
    cfg = load_config()
    # Return root_path and user's email_folder
    return jsonify({
        "root_path": cfg.root_path,
        "email_folder": current_user.email_folder or ""
    })


@bp.route("", methods=["POST"])
@login_required
def set_config():
    data = request.get_json(force=True, silent=True) or {}
    cfg = load_config()
    changed_path = False

    if "root_path" in data:
        new_path = str(data["root_path"]).strip()
        if new_path != cfg.root_path:
            cfg.root_path = new_path
            changed_path = True

    save_config(cfg)
    return jsonify({"ok": True, "path_changed": changed_path})

