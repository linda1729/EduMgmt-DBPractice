"""Student API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Department, Student
from ..repositories.student_repository import StudentRepository

bp = Blueprint("students_api", __name__)


def _serialize_student(student) -> Dict[str, Any]:
    # 功能：将学生 ORM 对象映射为统一的 API 输出结构。
    return {
        "sno": student.sno,
        "name": student.sname,
        "gender": student.gender,
        "birth_date": student.birth_date.isoformat() if student.birth_date else None,
        "department": student.dno,
        "enroll_year": student.enroll_year,
        "email": student.email,
        "phone": student.phone,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }


def _parse_birth_date(value: Any) -> Any:
    # 功能：校验并转换 birth_date 字段，统一为 date/None。
    if value in (None, ""):
        return None
    if isinstance(value, (datetime,)):
        return value.date()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError("birth_date must be in YYYY-MM-DD format") from exc


@bp.get("/")
def list_students():
    # 功能：按条件分页检索学生列表并返回总数。
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)
    department = request.args.get("department")
    enroll_year = request.args.get("enroll_year")
    keyword = request.args.get("q")

    enroll_year_int = int(enroll_year) if enroll_year else None

    students, total = StudentRepository.list(
        department=department,
        enroll_year=enroll_year_int,
        keyword=keyword,
        page=page,
        per_page=per_page,
    )
    return jsonify(
        {
            "items": [_serialize_student(student) for student in students],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@bp.post("/")
def create_student():
    # 功能：校验请求负载并创建新的学生记录。
    payload = request.get_json(silent=True) or {}
    required_fields = {"sno", "name", "gender", "enroll_year"}
    missing = [field for field in required_fields if field not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    gender = payload["gender"]
    if gender not in {"Male", "Female", "Other"}:
        return jsonify({"error": "gender must be one of Male/Female/Other"}), 400

    try:
        birth_date = _parse_birth_date(payload.get("birth_date"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        enroll_year = int(payload["enroll_year"])
    except (TypeError, ValueError):
        return jsonify({"error": "enroll_year must be an integer"}), 400

    data = {
        "sno": payload["sno"],
        "sname": payload["name"],
        "gender": gender,
        "birth_date": birth_date,
        "dno": payload.get("department"),
        "enroll_year": enroll_year,
        "email": payload.get("email"),
        "phone": payload.get("phone"),
    }

    try:
        student = StudentRepository.create(data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to create student", "details": str(exc.orig)}), 400

    return jsonify(_serialize_student(student)), 201


@bp.get("/<string:sno>")
def retrieve_student(sno: str):
    # 功能：按学号获取学生详情，找不到时返回 404。
    student = StudentRepository.get(sno)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(_serialize_student(student))


@bp.put("/<string:sno>")
def update_student(sno: str):
    # 功能：支持对学生资源执行 PUT 更新，含字段映射与校验。
    student = StudentRepository.get(sno)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    payload = request.get_json(silent=True) or {}
    allowed_fields = {
        "name": "sname",
        "gender": "gender",
        "birth_date": "birth_date",
        "department": "dno",
        "enroll_year": "enroll_year",
        "email": "email",
        "phone": "phone",
    }
    update_data: Dict[str, Any] = {}

    if "gender" in payload:
        gender = payload["gender"]
        if gender not in {"Male", "Female", "Other"}:
            return jsonify({"error": "gender must be one of Male/Female/Other"}), 400
        update_data["gender"] = gender

    if "birth_date" in payload:
        try:
            update_data["birth_date"] = _parse_birth_date(payload["birth_date"])
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    for public_key, model_key in allowed_fields.items():
        if public_key in {"gender", "birth_date"}:
            continue
        if public_key in payload and payload[public_key] is not None:
            update_data[model_key] = payload[public_key]
        elif public_key in payload and payload[public_key] is None:
            update_data[model_key] = None

    if "enroll_year" in payload:
        try:
            update_data["enroll_year"] = int(payload["enroll_year"])
        except (TypeError, ValueError):
            return jsonify({"error": "enroll_year must be an integer"}), 400

    if "name" in payload:
        update_data["sname"] = payload["name"]

    try:
        student = StudentRepository.update(student, update_data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to update student", "details": str(exc.orig)}), 400

    return jsonify(_serialize_student(student))


@bp.delete("/<string:sno>")
def delete_student(sno: str):
    # 功能：删除学生记录并返回删除状态 JSON。
    student = StudentRepository.get(sno)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    StudentRepository.delete(student)
    return jsonify({"status": "deleted"})


@bp.get("/meta")
def student_meta():
    """Return dropdown data and aggregated statistics for the student module."""
    departments = (
        db.session.execute(select(Department).order_by(Department.dname))
        .scalars()
        .all()
    )
    department_payload = [{"dno": dept.dno, "dname": dept.dname} for dept in departments]

    total = db.session.scalar(select(func.count()).select_from(Student)) or 0

    gender_rows = (
        db.session.execute(
            select(Student.gender, func.count())
            .group_by(Student.gender)
            .order_by(Student.gender)
        )
        .all()
    )
    gender_distribution = [
        {"label": gender or "Unknown", "value": int(count or 0)}
        for gender, count in gender_rows
    ]

    dept_rows = (
        db.session.execute(
            select(Department.dname, func.count(Student.sno))
            .join(Student, Student.dno == Department.dno, isouter=True)
            .group_by(Department.dname)
            .order_by(Department.dname)
        )
        .all()
    )
    dept_distribution = [
        {"label": dept or "未分配", "value": int(count or 0)}
        for dept, count in dept_rows
    ]

    return jsonify(
        {
            "departments": department_payload,
            "stats": {
                "total": int(total),
                "gender_distribution": gender_distribution,
                "department_distribution": dept_distribution,
            },
        }
    )
