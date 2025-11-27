"""Data access helpers for Classroom model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, selectinload

from ..extensions import db
from ..models import Classroom


class ClassroomRepository:
    """Encapsulate CRUD logic for classrooms."""

    @staticmethod
    def _apply_filters(
        query: Query,
        *,
        building: Optional[str],
        room_id: Optional[str],
        room_no: Optional[str],
        keyword: Optional[str],
    ) -> Query:
        # 功能：根据楼栋、教室编号、房间号或模糊关键字筛选教室。
        if building:
            query = query.filter(Classroom.building == building)
        if room_id:
            query = query.filter(Classroom.room_id.ilike(f"%{room_id}%"))
        if room_no:
            query = query.filter(Classroom.room_no.ilike(f"%{room_no}%"))
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(Classroom.building.ilike(like), Classroom.room_no.ilike(like), Classroom.room_id.ilike(like))
            )
        return query

    @classmethod
    def list(
        cls,
        *,
        building: Optional[str] = None,
        room_id: Optional[str] = None,
        room_no: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Classroom], int]:
        # 功能：分页查询教室列表。
        query = Classroom.query
        query = cls._apply_filters(
            query,
            building=building,
            room_id=room_id,
            room_no=room_no,
            keyword=keyword,
        )
        total = query.count()
        items = (
            query.options(selectinload(Classroom.teachings))
            .order_by(Classroom.building, Classroom.room_no)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def get(room_id: str) -> Optional[Classroom]:
        # 功能：按 room_id 获取教室。
        return db.session.get(Classroom, room_id)

    @staticmethod
    def create(data: Dict[str, Any]) -> Classroom:
        # 功能：新建教室记录。
        classroom = Classroom(**data)
        db.session.add(classroom)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return classroom

    @staticmethod
    def update(classroom: Classroom, data: Dict[str, Any]) -> Classroom:
        # 功能：更新教室属性。
        for key, value in data.items():
            setattr(classroom, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return classroom

    @staticmethod
    def delete(classroom: Classroom) -> None:
        # 功能：删除教室记录。
        db.session.delete(classroom)
        db.session.commit()
