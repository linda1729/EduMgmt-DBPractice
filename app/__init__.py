"""Application factory for the student academic management system."""

from __future__ import annotations

from typing import Iterable, Sequence

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate
from .api import register_api
from .routes import bp as main_bp
from .cli import register_cli_commands

# 在导入阶段加载 .env，确保 CLI / 测试环境也能获得变量
load_dotenv()


def _normalize_origins(value: Sequence[str] | str | None) -> list[str]:
    """Split comma-separated origin strings into a clean list."""
    if value is None:
        return []
    if isinstance(value, str):
        candidates: Iterable[str] = value.split(",")
    else:
        candidates = value
    return [item.strip() for item in candidates if item and item.strip()]


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create and configure the Flask application."""
    # 功能：构建并初始化 Flask 应用实例，同时注册扩展、蓝图与 CLI 命令。
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    cors_origins = _normalize_origins(app.config.get("CORS_ORIGINS"))
    if cors_origins:
        origins = "*" if "*" in cors_origins else cors_origins
    else:
        origins = "*"

    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so that metadata is registered with SQLAlchemy
    from . import models  # noqa: F401  # pylint: disable=unused-import

    # Register blueprints
    app.register_blueprint(main_bp)
    register_api(app)

    # CLI commands (e.g., init-db)
    register_cli_commands(app)

    return app
