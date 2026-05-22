from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from ..config import load_config

bp = Blueprint("main", __name__)


@bp.route("/app")
@login_required
def app_shell():
    return render_template("app.html")


@bp.route("/config")
@login_required
def config_page():
    return render_template("config.html")
