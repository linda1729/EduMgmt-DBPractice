"""Data access helpers for Course model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query

from ..extensions import db
from ..models import Course


class CourseRepository:
    """Encapsulate common Course queries."""

    @staticmethod
    def _apply_filters(query: Query, *, department: Optional[str], active_only: bool, keyword: Optional[str]) -> Query:
        # 功能：根据院系、上下架状态与关键字构建课程筛选条件。
        if department:
            query = query.filter(Course.dno == department)
        if active_only:
            query = query.filter(Course.is_active.is_(True))
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(Course.cname.ilike(like), Course.cno.ilike(like)))
        return query

    @classmethod
    def list(cls, *, department: Optional[str] = None, active_only: bool = True, keyword: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Course], int]:
        # 功能：分页查询课程并返回总记录数。
        query = Course.query
        query = cls._apply_filters(query, department=department, active_only=active_only, keyword=keyword)
        total = query.count()
        items = (
            query.order_by(Course.cno)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def get(cno: str) -> Optional[Course]:
        # 功能：按课程编号加载课程实例。
        return db.session.get(Course, cno)

    @staticmethod
    def create(data: Dict[str, Any]) -> Course:
        # 功能：新建课程记录并处理唯一性冲突。
        course = Course(**data)
        db.session.add(course)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return course

    @staticmethod
    def update(course: Course, data: Dict[str, Any]) -> Course:
        # 功能：更新课程字段后提交事务。
        for key, value in data.items():
            setattr(course, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return course

    @staticmethod
    def delete(course: Course) -> None:
        # 功能：删除课程记录并提交删除事务。
        db.session.delete(course)
        db.session.commit()
