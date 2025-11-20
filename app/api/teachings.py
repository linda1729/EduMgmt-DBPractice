"""Teaching assignment API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Classroom, Course, Teacher, Teaching, TermDict
from ..repositories.teaching_repository import TeachingRepository

bp = Blueprint("teachings_api", __name__)


def _parse_date(value: Optional[str]) -> Optional[datetime.date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Date must be in YYYY-MM-DD format")


def _serialize_teaching(teaching: Teaching) -> Dict[str, Any]:
    course = teaching.course
    teacher = teaching.teacher
    classroom = teaching.classroom
    return {
        "teach_id": teaching.teach_id,
        "course_id": teaching.cno,
        "course_name": course.cname if course else None,
        "teacher_id": teaching.tno,
        "teacher_name": teacher.tname if teacher else None,
        "year": teaching.year_offered,
        "term": teaching.term,
        "room_id": teaching.room_id,
        "classroom_label": f"{classroom.building} {classroom.room_no}" if classroom else None,
        "capacity": teaching.capacity,
        "start_date": teaching.start_date.strftime("%Y-%m-%d") if teaching.start_date else None,
        "end_date": teaching.end_date.strftime("%Y-%m-%d") if teaching.end_date else None,
    }


@bp.get("/")
def list_teachings():
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)
    course_id = request.args.get("course")
    teacher_id = request.args.get("teacher")
    term = request.args.get("term")
    year_raw = request.args.get("year")
    year = None
    if year_raw:
        try:
            year = int(year_raw)
        except ValueError:
            return jsonify({"error": "year must be an integer"}), 400

    teachings, total = TeachingRepository.list(
        course_id=course_id,
        teacher_id=teacher_id,
        term=term,
        year=year,
        page=page,
        per_page=per_page,
    )

    return jsonify(
        {
            "items": [_serialize_teaching(teaching) for teaching in teachings],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


def _load_course(cno: str) -> Course | None:
    return db.session.get(Course, cno)


def _load_teacher(tno: str) -> Teacher | None:
    return db.session.get(Teacher, tno)


def _load_classroom(room_id: Optional[str]) -> Classroom | None:
    if not room_id:
        return None
    return db.session.get(Classroom, room_id)


def _validate_foreign_keys(payload: Dict[str, Any]) -> Optional[str]:
    if not _load_course(payload["course_id"]):
        return "Course not found"
    if not _load_teacher(payload["teacher_id"]):
        return "Teacher not found"
    if not db.session.get(TermDict, payload["term"]):
        return "Term not found"
    room_id = payload.get("room_id")
    if room_id and not _load_classroom(room_id):
        return "Classroom not found"
    return None


def _teaching_payload_from_request() -> Dict[str, Any]:
    payload = request.get_json(silent=True) or {}
    required = {"course_id", "teacher_id", "year", "term"}
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")
    try:
        year = int(payload["year"])
    except (TypeError, ValueError) as exc:
        raise ValueError("year must be an integer") from exc
    data: Dict[str, Any] = {
        "cno": payload["course_id"],
        "tno": payload["teacher_id"],
        "year_offered": year,
        "term": payload["term"],
    }
    if "room_id" in payload:
        data["room_id"] = payload.get("room_id")
    if "capacity" in payload and payload["capacity"] is not None:
        try:
            data["capacity"] = int(payload["capacity"])
        except (TypeError, ValueError) as exc:
            raise ValueError("capacity must be an integer") from exc
    if "start_date" in payload:
        data["start_date"] = _parse_date(payload["start_date"])
    if "end_date" in payload:
        data["end_date"] = _parse_date(payload["end_date"])
    return data


@bp.post("/")
def create_teaching():
    try:
        data = _teaching_payload_from_request()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    fk_error = _validate_foreign_keys(
        {
            "course_id": data["cno"],
            "teacher_id": data["tno"],
            "term": data["term"],
            "room_id": data.get("room_id"),
        }
    )
    if fk_error:
        return jsonify({"error": fk_error}), 404

    try:
        teaching = TeachingRepository.create(data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to create teaching", "details": str(exc.orig)}), 400

    # reload relationships for serialization
    db.session.refresh(teaching)
    return jsonify(_serialize_teaching(teaching)), 201


@bp.get("/<int:teach_id>")
def retrieve_teaching(teach_id: int):
    teaching = TeachingRepository.get(teach_id)
    if not teaching:
        return jsonify({"error": "Teaching not found"}), 404
    return jsonify(_serialize_teaching(teaching))


@bp.put("/<int:teach_id>")
def update_teaching(teach_id: int):
    teaching = TeachingRepository.get(teach_id)
    if not teaching:
        return jsonify({"error": "Teaching not found"}), 404

    payload = request.get_json(silent=True) or {}
    update_data: Dict[str, Any] = {}

    if "course_id" in payload:
        if not _load_course(payload["course_id"]):
            return jsonify({"error": "Course not found"}), 404
        update_data["cno"] = payload["course_id"]

    if "teacher_id" in payload:
        if not _load_teacher(payload["teacher_id"]):
            return jsonify({"error": "Teacher not found"}), 404
        update_data["tno"] = payload["teacher_id"]

    if "term" in payload:
        if not db.session.get(TermDict, payload["term"]):
            return jsonify({"error": "Term not found"}), 404
        update_data["term"] = payload["term"]

    if "year" in payload:
        try:
            update_data["year_offered"] = int(payload["year"])
        except (TypeError, ValueError):
            return jsonify({"error": "year must be an integer"}), 400

    if "room_id" in payload:
        room_id = payload["room_id"]
        if room_id and not _load_classroom(room_id):
            return jsonify({"error": "Classroom not found"}), 404
        update_data["room_id"] = room_id

    if "capacity" in payload:
        try:
            update_data["capacity"] = int(payload["capacity"])
        except (TypeError, ValueError):
            return jsonify({"error": "capacity must be an integer"}), 400

    for field in ("start_date", "end_date"):
        if field in payload:
            try:
                update_data[field] = _parse_date(payload[field])
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400

    try:
        teaching = TeachingRepository.update(teaching, update_data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to update teaching", "details": str(exc.orig)}), 400

    db.session.refresh(teaching)
    return jsonify(_serialize_teaching(teaching))


@bp.delete("/<int:teach_id>")
def delete_teaching(teach_id: int):
    teaching = TeachingRepository.get(teach_id)
    if not teaching:
        return jsonify({"error": "Teaching not found"}), 404
    TeachingRepository.delete(teaching)
    return jsonify({"status": "deleted"})


@bp.get("/meta")
def teaching_meta():
    """Return dropdown data and aggregated stats."""
    courses = (
        db.session.execute(select(Course).order_by(Course.cname))
        .scalars()
        .all()
    )
    teachers = (
        db.session.execute(select(Teacher).order_by(Teacher.tname))
        .scalars()
        .all()
    )
    classrooms = (
        db.session.execute(select(Classroom).order_by(Classroom.building, Classroom.room_no))
        .scalars()
        .all()
    )
    terms = (
        db.session.execute(select(TermDict).order_by(TermDict.term_code))
        .scalars()
        .all()
    )

    total = db.session.scalar(select(func.count()).select_from(Teaching)) or 0
    avg_capacity = db.session.scalar(select(func.avg(Teaching.capacity))) or 0
    term_rows = (
        db.session.execute(
            select(Teaching.term, func.count())
            .group_by(Teaching.term)
            .order_by(Teaching.term)
        )
        .all()
    )
    term_distribution = [
        {"label": term, "value": int(count or 0)} for term, count in term_rows
    ]

    return jsonify(
        {
            "courses": [{"cno": course.cno, "cname": course.cname} for course in courses],
            "teachers": [
                {"tno": teacher.tno, "tname": teacher.tname, "title": teacher.title}
                for teacher in teachers
            ],
            "classrooms": [
                {
                    "room_id": classroom.room_id,
                    "label": f"{classroom.building} {classroom.room_no}",
                }
                for classroom in classrooms
            ],
            "terms": [
                {"term_code": term.term_code, "term_name": term.term_name} for term in terms
            ],
            "stats": {
                "total": int(total),
                "average_capacity": round(float(avg_capacity), 2) if avg_capacity else 0,
                "term_distribution": term_distribution,
            },
        }
    )
