"""Helpers for importing the MySQL schema into the configured database."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pymysql
from flask import current_app
from sqlalchemy.engine.url import make_url

logger = logging.getLogger(__name__)


def _iter_statements(sql_text: str) -> Iterable[str]:
    """Yield executable SQL statements, honoring custom delimiter blocks."""
    # 功能：解析 SQL 文本并按分隔符逐条产出可执行语句，兼容自定义 DELIMITER。

    delimiter = ";"
    statement_lines: list[str] = []

    for raw_line in sql_text.splitlines(keepends=True):
        stripped = raw_line.strip()

        # Handle delimiter directives (e.g., DELIMITER $$)
        if stripped.upper().startswith("DELIMITER"):
            parts = stripped.split()
            delimiter = parts[1] if len(parts) > 1 else ";"
            continue

        statement_lines.append(raw_line)

        if stripped.endswith(delimiter):
            statement = "".join(statement_lines).strip()
            statement_lines.clear()

            if not statement:
                continue

            if delimiter != ";":
                # Replace trailing custom delimiter with a standard semicolon
                if statement.endswith(delimiter):
                    statement = f"{statement[: -len(delimiter)]};"
            yield statement

    # Flush remainder if file doesn't end with delimiter
    trailing = "".join(statement_lines).strip()
    if trailing:
        if trailing.endswith(delimiter) and delimiter != ";":
            trailing = f"{trailing[: -len(delimiter)]};"
        if not trailing.endswith(";"):
            trailing = f"{trailing};"
        yield trailing


def load_schema() -> None:
    """Execute schema.sql against the configured MySQL server."""
    # 功能：读取 schema.sql 并通过 PyMySQL 在目标 MySQL 实例中重建结构。
    app = current_app
    schema_path: Path = app.config["SCHEMA_PATH"]

    if not schema_path.exists():
        raise FileNotFoundError(f"schema.sql not found at {schema_path}")

    sql_text = schema_path.read_text(encoding="utf-8")
    statements = list(_iter_statements(sql_text))
    if not statements:
        raise ValueError("schema.sql is empty or could not be parsed into statements.")

    url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])

    connection = pymysql.connect(
        host=url.host or "127.0.0.1",
        port=url.port or 3306,
        user=url.username or "",
        password=url.password or "",
        charset="utf8mb4",
        autocommit=True,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
    )

    try:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
    finally:
        connection.close()

    app.logger.info("Database schema applied from %s", schema_path)
