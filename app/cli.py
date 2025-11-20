"""Custom Flask CLI commands."""

from __future__ import annotations

import click
from flask import Flask
from flask.cli import with_appcontext

from .db_init import load_schema
from .services import populate_sample_data
from .extensions import db


def register_cli_commands(app: Flask) -> None:
    """Attach custom management commands to the Flask CLI."""
    # 功能：在 Flask CLI 中注册初始化数据库和填充演示数据的自定义命令。

    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command() -> None:
        """Import schema.sql into the configured MySQL instance."""
        # 功能：执行 schema.sql 初始化数据库结构。
        load_schema()
        click.echo("Database initialized with schema.sql")

    @app.cli.command("seed-demo")
    @with_appcontext
    def seed_demo_command() -> None:
        """Populate the database with synthetic demo data."""
        # 功能：调用种子服务批量写入演示数据。
        populate_sample_data()
        click.echo("Demo data seeded (approximately 100 rows per table).")

    @app.cli.command("check-db")
    @with_appcontext
    def check_db_command() -> None:
        """Validate database connectivity with a lightweight SELECT 1."""
        # 功能：执行简单查询检测数据库/凭据是否可用。
        db.session.execute(db.text("SELECT 1"))
        click.echo("Database connection OK.")
