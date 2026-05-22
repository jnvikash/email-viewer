from flask import Flask, redirect, url_for
from flask_login import login_required
from .config import load_config
from .db import init_db
from .auth import bp as auth_bp, login_manager


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    cfg = load_config()
    app.config["SECRET_KEY"] = cfg.secret_key
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True

    init_db()

    login_manager.init_app(app)

    app.register_blueprint(auth_bp)

    from .routes import api_config, api_folders, api_emails, api_attachments, api_search, api_index, main, admin
    app.register_blueprint(api_config.bp)
    app.register_blueprint(api_folders.bp)
    app.register_blueprint(api_emails.bp)
    app.register_blueprint(api_attachments.bp)
    app.register_blueprint(api_search.bp)
    app.register_blueprint(api_index.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(main.bp)

    @app.route("/")
    def index():
        return redirect(url_for("main.app_shell"))

    return app
