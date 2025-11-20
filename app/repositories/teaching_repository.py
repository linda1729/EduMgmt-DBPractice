"""Data access helpers for Teaching model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, selectinload

from ..extensions import db
from ..models import Teaching


class TeachingRepository:
    """Encapsulate CRUD logic for Teaching assignments."""

    @staticmethod
    def _apply_filters(
        query: Query,
        *,
        course_id: Optional[str],
        teacher_id: Optional[str],
        term: Optional[str],
        year: Optional[int],
    ) -> Query:
        # 功能：按课程、教师、学期、学年过滤授课安排。
        if course_id:
            query = query.filter(Teaching.cno == course_id)
        if teacher_id:
            query = query.filter(Teaching.tno == teacher_id)
        if term:
            query = query.filter(Teaching.term == term)
        if year:
            query = query.filter(Teaching.year_offered == year)
        return query

    @classmethod
    def list(
        cls,
        *,
        course_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
        term: Optional[str] = None,
        year: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Teaching], int]:
        # 功能：分页查询授课安排并返回总数。
        query = Teaching.query.options(
            selectinload(Teaching.course),
            selectinload(Teaching.teacher),
            selectinload(Teaching.classroom),
        )
        query = cls._apply_filters(query, course_id=course_id, teacher_id=teacher_id, term=term, year=year)
        total = query.count()
        items = (
            query.order_by(Teaching.year_offered.desc(), Teaching.term.desc(), Teaching.teach_id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def get(teach_id: int) -> Optional[Teaching]:
        # 功能：按主键加载授课安排。
        return db.session.get(Teaching, teach_id)

    @staticmethod
    def create(data: Dict[str, Any]) -> Teaching:
        # 功能：创建授课记录。
        teaching = Teaching(**data)
        db.session.add(teaching)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return teaching

    @staticmethod
    def update(teaching: Teaching, data: Dict[str, Any]) -> Teaching:
        # 功能：更新授课字段。
        for key, value in data.items():
            setattr(teaching, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return teaching

    @staticmethod
    def delete(teaching: Teaching) -> None:
        # 功能：删除授课安排。
        db.session.delete(teaching)
        db.session.commit()
