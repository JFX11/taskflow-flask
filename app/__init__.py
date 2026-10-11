"""Фабрика приложения: настройка Flask, базы данных и маршрутов."""

import os
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key"),
        DATABASE=os.environ.get("DATABASE", str(Path(app.instance_path) / "tasks.sqlite")),
        MAX_CONTENT_LENGTH=16 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    CSRFProtect(app)
    from .routes import bp

    app.register_blueprint(bp)
    with app.app_context():
        db.init_db()
    return app
