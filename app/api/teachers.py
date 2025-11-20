"""Teacher API endpoints."""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..constants import (
    ENTITY_PK_DUP_MSG,
    ENTITY_PK_EMPTY_MSG,
    REFERENTIAL_DEPARTMENT_MSG,
    TEACHER_TITLES,
)
from ..extensions import db
from ..models import Department, Teacher
from ..repositories.teacher_repository import TeacherRepository

bp = Blueprint("teachers_api", __name__)


def _serialize_teacher(teacher: Teacher) -> Dict[str, Any]:
    return {
        "tno": teacher.tno,
        "name": teacher.tname,
        "title": teacher.title,
        "department": teacher.dno,
        "department_name": teacher.department.dname if teacher.department else None,
        "email": teacher.email,
        "phone": teacher.phone,
        "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
        "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
    }


@bp.get("/")
def list_teachers():
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)
    department = request.args.get("department")
    title = request.args.get("title")
    keyword = request.args.get("q")
    name_filter = request.args.get("name")
    email_filter = request.args.get("email")
    phone_filter = request.args.get("phone")

    teachers, total = TeacherRepository.list(
        department=department,
        title=title,
        name=name_filter,
        email=email_filter,
        phone=phone_filter,
        keyword=keyword,
        page=page,
        per_page=per_page,
    )
    return jsonify(
        {
            "items": [_serialize_teacher(teacher) for teacher in teachers],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@bp.post("/")
def create_teacher():
    payload = request.get_json(silent=True) or {}
    required = {"tno", "name", "title"}
    missing = [field for field in required if field not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    tno = str(payload["tno"]).strip()
    if not tno:
        return jsonify({"error": ENTITY_PK_EMPTY_MSG}), 400
    if TeacherRepository.get(tno):
        return jsonify({"error": ENTITY_PK_DUP_MSG}), 400

    title = payload["title"]
    if title not in TEACHER_TITLES:
        return jsonify({"error": "Invalid teacher title"}), 400
    department = payload.get("department")
    if department and not db.session.get(Department, department):
        return jsonify({"error": REFERENTIAL_DEPARTMENT_MSG}), 400

    data = {
        "tno": tno,
        "tname": payload["name"],
        "title": title,
        "dno": department,
        "email": payload.get("email"),
        "phone": payload.get("phone"),
    }
    try:
        teacher = TeacherRepository.create(data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to create teacher", "details": str(exc.orig)}), 400

    return jsonify(_serialize_teacher(teacher)), 201


@bp.get("/<string:tno>")
def retrieve_teacher(tno: str):
    teacher = TeacherRepository.get(tno)
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
    return jsonify(_serialize_teacher(teacher))


@bp.put("/<string:tno>")
def update_teacher(tno: str):
    teacher = TeacherRepository.get(tno)
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    payload = request.get_json(silent=True) or {}
    update_data: Dict[str, Any] = {}

    if "name" in payload:
        update_data["tname"] = payload["name"]

    if "title" in payload:
        title = payload["title"]
        if title not in TEACHER_TITLES:
            return jsonify({"error": "Invalid teacher title"}), 400
        update_data["title"] = title

    if "department" in payload:
        department = payload["department"]
        if department and not db.session.get(Department, department):
            return jsonify({"error": REFERENTIAL_DEPARTMENT_MSG}), 400
        update_data["dno"] = department

    for field in ("email", "phone"):
        if field in payload:
            update_data[field] = payload[field]

    try:
        teacher = TeacherRepository.update(teacher, update_data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to update teacher", "details": str(exc.orig)}), 400

    return jsonify(_serialize_teacher(teacher))


@bp.delete("/<string:tno>")
def delete_teacher(tno: str):
    teacher = TeacherRepository.get(tno)
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
    TeacherRepository.delete(teacher)
    return jsonify({"status": "deleted"})


@bp.get("/meta")
def teacher_meta():
    """Return dropdown options and aggregated stats."""
    departments = (
        db.session.execute(select(Department).order_by(Department.dname))
        .scalars()
        .all()
    )
    department_payload = [
        {"dno": dept.dno, "dname": dept.dname} for dept in departments
    ]

    teacher_total = db.session.scalar(select(func.count()).select_from(Teacher)) or 0
    title_rows = (
        db.session.execute(
            select(Teacher.title, func.count())
            .group_by(Teacher.title)
            .order_by(Teacher.title)
        )
        .all()
    )
    title_distribution = [
        {"label": title, "value": int(count or 0)} for title, count in title_rows
    ]

    return jsonify(
        {
            "departments": department_payload,
            "titles": TEACHER_TITLES,
            "stats": {
                "total": int(teacher_total),
                "title_distribution": title_distribution,
            },
        }
    )
