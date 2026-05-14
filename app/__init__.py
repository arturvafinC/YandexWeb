import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from app.config import Config
from app.db import db
from app.models import User


login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Войдите, чтобы открыть эту страницу."

    configure_logging(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def configure_logging(app):
    if any(isinstance(handler, RotatingFileHandler) for handler in app.logger.handlers):
        return
    handler = RotatingFileHandler("logs/app.log", maxBytes=500_000, backupCount=3, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def register_blueprints(app):
    from app.api.routes import api_bp
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.mistakes.routes import mistakes_bp

    csrf.exempt(api_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(mistakes_bp)
    app.register_blueprint(api_bp)


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden"}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Mistake not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Server error")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html"), 500
