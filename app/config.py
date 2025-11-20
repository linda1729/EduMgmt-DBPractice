"""Configuration objects for the Flask application."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_SCHEMA_PATH = BASE_DIR / "SQL" / "schema.sql"
DEFAULT_SQLITE_URI = f"sqlite:///{(INSTANCE_DIR / 'dev.db').as_posix()}"


class Config:
    """Default configuration pulls values from environment variables."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Database connection string（默认退回仓库内置的 SQLite，便于即开即用）
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URI", DEFAULT_SQLITE_URI)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "echo": False,
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Absolute path to schema.sql so CLI import can locate it reliably
    _schema_override = os.environ.get("SCHEMA_PATH")
    SCHEMA_PATH: Path = (
        Path(_schema_override).expanduser().resolve()
        if _schema_override
        else DEFAULT_SCHEMA_PATH
    )

    # 允许的前端来源，供 Flask-CORS 使用，逗号分隔
    CORS_ORIGINS: str = os.environ.get(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://localhost:4173",
    )
