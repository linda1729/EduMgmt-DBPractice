"""Course API endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Course, Department
from ..repositories.course_repository import CourseRepository

bp = Blueprint("courses_api", __name__)


def _serialize_course(course: Course) -> Dict[str, Any]:
    # 功能：格式化课程 ORM 数据为 API JSON 输出。
    return {
        "cno": course.cno,
        "name": course.cname,
        "credits": course.credits,
        "hours": course.hours,
        "department": course.dno,
        "prerequisite": course.prereq_cno,
        "is_active": course.is_active,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
    }


def _parse_int(name: str, value: Any, minimum: Optional[int] = None, maximum: Optional[int] = None) -> int:
    # 功能：通用整型解析器，负责限定上下界并输出 int。
    try:
        ivalue = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if minimum is not None and ivalue < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and ivalue > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return ivalue


@bp.get("/")
def list_courses():
    # 功能：分页查询课程列表并支持按院系/关键字筛选。
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)
    department = request.args.get("department")
    keyword = request.args.get("q")
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    courses, total = CourseRepository.list(
        department=department,
        active_only=not include_inactive,
        keyword=keyword,
        page=page,
        per_page=per_page,
    )

    return jsonify(
        {
            "items": [_serialize_course(course) for course in courses],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@bp.post("/")
def create_course():
    # 功能：创建课程资源，包含字段校验与错误返回。
    payload = request.get_json(silent=True) or {}
    required_fields = {"cno", "name", "credits", "hours"}
    missing = [field for field in required_fields if field not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        credits = _parse_int("credits", payload["credits"], minimum=1)
        hours = _parse_int("hours", payload["hours"], minimum=1)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    data = {
        "cno": payload["cno"],
        "cname": payload["name"],
        "credits": credits,
        "hours": hours,
        "dno": payload.get("department"),
        "prereq_cno": payload.get("prerequisite"),
        "is_active": bool(payload.get("is_active", True)),
    }

    try:
        course = CourseRepository.create(data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to create course", "details": str(exc.orig)}), 400

    return jsonify(_serialize_course(course)), 201


@bp.get("/<string:cno>")
def retrieve_course(cno: str):
    # 功能：根据课程编号返回详情，缺失时返回 404。
    course = CourseRepository.get(cno)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(_serialize_course(course))


@bp.put("/<string:cno>")
def update_course(cno: str):
    # 功能：允许局部更新课程信息并处理合法性校验。
    course = CourseRepository.get(cno)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    payload = request.get_json(silent=True) or {}
    update_data: Dict[str, Any] = {}

    if "name" in payload:
        update_data["cname"] = payload["name"]
    if "department" in payload:
        update_data["dno"] = payload["department"]
    if "prerequisite" in payload:
        update_data["prereq_cno"] = payload["prerequisite"]
    if "is_active" in payload:
        update_data["is_active"] = bool(payload["is_active"])

    if "credits" in payload:
        try:
            update_data["credits"] = _parse_int("credits", payload["credits"], minimum=1)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    if "hours" in payload:
        try:
            update_data["hours"] = _parse_int("hours", payload["hours"], minimum=1)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    try:
        course = CourseRepository.update(course, update_data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to update course", "details": str(exc.orig)}), 400

    return jsonify(_serialize_course(course))


@bp.delete("/<string:cno>")
def delete_course(cno: str):
    # 功能：删除课程，若存在选课依赖则阻止操作。
    course = CourseRepository.get(cno)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if course.enrollments:
        return jsonify({"error": "Cannot delete course with enrollments"}), 400

    CourseRepository.delete(course)
    return jsonify({"status": "deleted"})


@bp.get("/meta")
def course_meta():
    """Return dropdown data and aggregated statistics for course management."""
    departments = (
        db.session.execute(select(Department).order_by(Department.dname))
        .scalars()
        .all()
    )
    department_payload = [{"dno": dept.dno, "dname": dept.dname} for dept in departments]

    all_courses = (
        db.session.execute(select(Course).order_by(Course.cname))
        .scalars()
        .all()
    )
    course_options = [{"cno": course.cno, "cname": course.cname} for course in all_courses]

    total = db.session.scalar(select(func.count()).select_from(Course)) or 0
    active = (
        db.session.scalar(
            select(func.count()).select_from(Course).where(Course.is_active.is_(True))
        )
        or 0
    )
    avg_credit = db.session.scalar(select(func.avg(Course.credits))) or 0
    dept_rows = (
        db.session.execute(
            select(Department.dname, func.count(Course.cno))
            .join(Course, Course.dno == Department.dno, isouter=True)
            .group_by(Department.dname)
            .order_by(Department.dname)
        )
        .all()
    )
    dept_distribution = [
        {"label": dept or "未分配", "value": int(count or 0)} for dept, count in dept_rows
    ]

    return jsonify(
        {
            "departments": department_payload,
            "courses": course_options,
            "stats": {
                "total": int(total),
                "active": int(active),
                "average_credit": round(float(avg_credit), 2) if avg_credit else 0,
                "department_distribution": dept_distribution,
            },
        }
    )
