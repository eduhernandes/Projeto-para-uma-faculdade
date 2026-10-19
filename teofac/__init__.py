from pathlib import Path
from logging.handlers import RotatingFileHandler
import logging, os
from flask import Flask, render_template, g, request
from .config import get_config
from .extensions import csrf, db, limiter, migrate


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name or os.getenv("FLASK_ENV", "development")))
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app); migrate.init_app(app, db); csrf.init_app(app); limiter.init_app(app)
    from . import models  # noqa: F401
    from .services.auth import load_current_user
    from .blueprints.main import main_bp
    from .blueprints.auth import auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.teacher import teacher_bp
    from .blueprints.student import student_bp
    from .blueprints.errors import errors_bp
    app.register_blueprint(errors_bp); app.register_blueprint(main_bp); app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp); app.register_blueprint(teacher_bp); app.register_blueprint(student_bp)
    app.before_request(load_current_user)
    @app.context_processor
    def inject_globals():
        return {"current_user": getattr(g, "current_user", None), "app_name": app.config["APP_NAME"]}
    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")
        if request.endpoint and not request.endpoint.startswith("static") and g.get("current_user"):
            response.headers.setdefault("Cache-Control", "no-store")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
    if not app.debug and not app.testing:
        log_dir = Path(app.instance_path) / "logs"; log_dir.mkdir(exist_ok=True)
        handler = RotatingFileHandler(log_dir / "teofac.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")); app.logger.addHandler(handler)
    from .cli import register_commands
    register_commands(app)
    return app
