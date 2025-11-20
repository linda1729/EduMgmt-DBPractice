"""Enrollment (SC) API endpoints."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..constants import (
    ENTITY_PK_DUP_MSG,
    ENTITY_PK_EMPTY_MSG,
    REFERENTIAL_STUDENT_COURSE_MSG,
)
from ..extensions import db
from ..models import Course, Enrollment, Student, TermDict
from ..repositories.course_repository import CourseRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..repositories.student_repository import StudentRepository

bp = Blueprint("enrollments_api", __name__)

ALLOWED_STATUS = {"enrolled", "dropped", "completed"}


def _serialize_enrollment(enrollment: Enrollment) -> Dict[str, Any]:
    # 功能：将选课 ORM 对象序列化为 API 可消费的字典。
    return {
        "student_id": enrollment.sno,
        "course_id": enrollment.cno,
        "year": enrollment.year_taken,
        "term": enrollment.term,
        "grade": float(enrollment.grade) if enrollment.grade is not None else None,
        "status": enrollment.status,
        "enroll_date": enrollment.enroll_date.isoformat() if enrollment.enroll_date else None,
        "updated_at": enrollment.updated_at.isoformat() if enrollment.updated_at else None,
    }


def _parse_grade(value: Any) -> Decimal:
    # 功能：校验成绩字段并规范到 0-100 区间内的 Decimal。
    if value in (None, ""):
        raise ValueError("grade cannot be empty")
    try:
        grade = Decimal(str(value))
    except Exception as exc:  # noqa: BLE001 - capture conversion errors
        raise ValueError("grade must be a number") from exc
    if grade < 0 or grade > 100:
        raise ValueError("grade must be between 0 and 100")
    return grade


@bp.get("/")
def list_enrollments():
    # 功能：按学生、课程、状态等条件分页查询选课记录。
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)
    student_id = request.args.get("student")
    course_id = request.args.get("course")
    status = request.args.get("status")
    year = request.args.get("year")
    term = request.args.get("term")
    keyword = request.args.get("q")

    year_int = int(year) if year else None

    enrollments, total = EnrollmentRepository.list(
        student_id=student_id,
        course_id=course_id,
        status=status,
        year=year_int,
        term=term,
        keyword=keyword,
        page=page,
        per_page=per_page,
    )

    return jsonify(
        {
            "items": [_serialize_enrollment(item) for item in enrollments],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@bp.post("/")
def create_enrollment():
    # 功能：校验前置条件与成绩后创建新的选课记录。
    payload = request.get_json(silent=True) or {}
    required = {"student_id", "course_id", "year", "term"}
    missing = [field for field in required if field not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    sno = str(payload["student_id"]).strip()
    cno = str(payload["course_id"]).strip()
    if not sno or not cno:
        return jsonify({"error": ENTITY_PK_EMPTY_MSG}), 400

    student = StudentRepository.get(sno)
    course = CourseRepository.get(cno)
    if not student or not course:
        return jsonify({"error": REFERENTIAL_STUDENT_COURSE_MSG}), 400

    if EnrollmentRepository.exists(sno, cno):
        return jsonify({"error": ENTITY_PK_DUP_MSG}), 400

    if not EnrollmentRepository.prerequisite_satisfied(sno, course):
        return jsonify({"error": "Prerequisite not satisfied"}), 400

    try:
        year = int(payload["year"])
    except (TypeError, ValueError):
        return jsonify({"error": "year must be an integer"}), 400

    term = payload["term"]
    if not term:
        return jsonify({"error": "term is required"}), 400

    status = payload.get("status", "enrolled")
    if status not in ALLOWED_STATUS:
        return jsonify({"error": f"status must be one of {', '.join(sorted(ALLOWED_STATUS))}"}), 400

    grade_value = payload.get("grade")
    if grade_value is not None:
        try:
            grade = _parse_grade(grade_value)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    else:
        grade = None

    data = {
        "sno": sno,
        "cno": cno,
        "year_taken": year,
        "term": term,
        "status": status,
        "grade": grade,
    }

    try:
        enrollment = EnrollmentRepository.create(data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to create enrollment", "details": str(exc.orig)}), 400

    return jsonify(_serialize_enrollment(enrollment)), 201


@bp.get("/<string:sno>/<string:cno>")
def retrieve_enrollment(sno: str, cno: str):
    # 功能：返回指定学生与课程的选课详情。
    enrollment = EnrollmentRepository.get(sno, cno)
    if not enrollment:
        return jsonify({"error": "Enrollment not found"}), 404
    return jsonify(_serialize_enrollment(enrollment))


@bp.put("/<string:sno>/<string:cno>")
def update_enrollment(sno: str, cno: str):
    # 功能：允许更新选课状态、成绩及时间信息。
    enrollment = EnrollmentRepository.get(sno, cno)
    if not enrollment:
        return jsonify({"error": "Enrollment not found"}), 404

    payload = request.get_json(silent=True) or {}
    update_data: Dict[str, Any] = {}

    if "status" in payload:
        status = payload["status"]
        if status not in ALLOWED_STATUS:
            return jsonify({"error": f"status must be one of {', '.join(sorted(ALLOWED_STATUS))}"}), 400
        update_data["status"] = status

    if "grade" in payload:
        grade_input = payload["grade"]
        if grade_input is None:
            update_data["grade"] = None
        else:
            try:
                update_data["grade"] = _parse_grade(grade_input)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400

    if "year" in payload:
        try:
            update_data["year_taken"] = int(payload["year"])
        except (TypeError, ValueError):
            return jsonify({"error": "year must be an integer"}), 400

    if "term" in payload:
        if not payload["term"]:
            return jsonify({"error": "term cannot be empty"}), 400
        update_data["term"] = payload["term"]

    try:
        enrollment = EnrollmentRepository.update(enrollment, update_data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to update enrollment", "details": str(exc.orig)}), 400

    return jsonify(_serialize_enrollment(enrollment))


@bp.delete("/<string:sno>/<string:cno>")
def delete_enrollment(sno: str, cno: str):
    # 功能：删除选课记录并返回统一删除响应。
    enrollment = EnrollmentRepository.get(sno, cno)
    if not enrollment:
        return jsonify({"error": "Enrollment not found"}), 404

    EnrollmentRepository.delete(enrollment)
    return jsonify({"status": "deleted"})


@bp.get("/meta")
def enrollment_meta():
    """Return dropdown options and stats for enrollment management."""
    students = (
        db.session.execute(select(Student).order_by(Student.sname))
        .scalars()
        .all()
    )
    courses = (
        db.session.execute(select(Course).order_by(Course.cname))
        .scalars()
        .all()
    )
    terms = (
        db.session.execute(select(TermDict).order_by(TermDict.term_code))
        .scalars()
        .all()
    )

    total = db.session.scalar(select(func.count()).select_from(Enrollment)) or 0
    status_rows = (
        db.session.execute(
            select(Enrollment.status, func.count())
            .group_by(Enrollment.status)
            .order_by(Enrollment.status)
        )
        .all()
    )
    status_distribution = [
        {"label": status, "value": int(count or 0)} for status, count in status_rows
    ]

    return jsonify(
        {
            "students": [
                {"sno": student.sno, "sname": student.sname} for student in students
            ],
            "courses": [{"cno": course.cno, "cname": course.cname} for course in courses],
            "terms": [
                {"term_code": term.term_code, "term_name": term.term_name} for term in terms
            ],
            "statuses": sorted(ALLOWED_STATUS),
            "stats": {
                "total": int(total),
                "status_distribution": status_distribution,
            },
        }
    )
