"""Classroom API endpoints."""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..constants import ENTITY_PK_DUP_MSG, ENTITY_PK_EMPTY_MSG
from ..extensions import db
from ..models import Classroom
from ..repositories.classroom_repository import ClassroomRepository

bp = Blueprint("classrooms_api", __name__)


def _serialize_classroom(classroom: Classroom) -> Dict[str, Any]:
    return {
        "room_id": classroom.room_id,
        "building": classroom.building,
        "room_no": classroom.room_no,
        "capacity": classroom.capacity,
    }


@bp.get("/")
def list_classrooms():
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)
    building = request.args.get("building")
    room_id = request.args.get("room_id")
    room_no = request.args.get("room_no")
    keyword = request.args.get("q")

    classrooms, total = ClassroomRepository.list(
        building=building,
        room_id=room_id,
        room_no=room_no,
        keyword=keyword,
        page=page,
        per_page=per_page,
    )
    return jsonify(
        {
            "items": [_serialize_classroom(classroom) for classroom in classrooms],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@bp.post("/")
def create_classroom():
    payload = request.get_json(silent=True) or {}
    required = {"room_id", "building", "room_no", "capacity"}
    missing = [field for field in required if field not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    room_id = str(payload["room_id"]).strip()
    if not room_id:
        return jsonify({"error": ENTITY_PK_EMPTY_MSG}), 400
    if ClassroomRepository.get(room_id):
        return jsonify({"error": ENTITY_PK_DUP_MSG}), 400

    try:
        capacity = int(payload["capacity"])
    except (TypeError, ValueError):
        return jsonify({"error": "capacity must be an integer"}), 400

    data = {
        "room_id": room_id,
        "building": payload["building"],
        "room_no": payload["room_no"],
        "capacity": capacity,
    }

    try:
        classroom = ClassroomRepository.create(data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to create classroom", "details": str(exc.orig)}), 400

    return jsonify(_serialize_classroom(classroom)), 201


@bp.get("/<string:room_id>")
def retrieve_classroom(room_id: str):
    classroom = ClassroomRepository.get(room_id)
    if not classroom:
        return jsonify({"error": "Classroom not found"}), 404
    return jsonify(_serialize_classroom(classroom))


@bp.put("/<string:room_id>")
def update_classroom(room_id: str):
    classroom = ClassroomRepository.get(room_id)
    if not classroom:
        return jsonify({"error": "Classroom not found"}), 404

    payload = request.get_json(silent=True) or {}
    update_data: Dict[str, Any] = {}

    for field in ("building", "room_no"):
        if field in payload:
            update_data[field] = payload[field]

    if "capacity" in payload:
        try:
            update_data["capacity"] = int(payload["capacity"])
        except (TypeError, ValueError):
            return jsonify({"error": "capacity must be an integer"}), 400

    try:
        classroom = ClassroomRepository.update(classroom, update_data)
    except IntegrityError as exc:
        return jsonify({"error": "Failed to update classroom", "details": str(exc.orig)}), 400

    return jsonify(_serialize_classroom(classroom))


@bp.delete("/<string:room_id>")
def delete_classroom(room_id: str):
    classroom = ClassroomRepository.get(room_id)
    if not classroom:
        return jsonify({"error": "Classroom not found"}), 404
    ClassroomRepository.delete(classroom)
    return jsonify({"status": "deleted"})


@bp.get("/meta")
def classroom_meta():
    """Return aggregated stats for dashboards/icons."""
    total = db.session.scalar(select(func.count()).select_from(Classroom)) or 0
    avg_capacity = db.session.scalar(select(func.avg(Classroom.capacity))) or 0
    building_rows = (
        db.session.execute(
            select(Classroom.building, func.count())
            .group_by(Classroom.building)
            .order_by(Classroom.building)
        )
        .all()
    )
    building_distribution = [
        {"label": building, "value": int(count or 0)}
        for building, count in building_rows
    ]

    return jsonify(
        {
            "stats": {
                "total": int(total),
                "average_capacity": round(float(avg_capacity), 2) if avg_capacity else 0,
                "building_distribution": building_distribution,
            }
        }
    )
