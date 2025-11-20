"""Data access helpers for Teacher model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, selectinload

from ..extensions import db
from ..models import Teacher


class TeacherRepository:
    """Encapsulate common Teacher queries."""

    @staticmethod
    def _apply_filters(
        query: Query,
        *,
        department: Optional[str],
        title: Optional[str],
        name: Optional[str],
        email: Optional[str],
        phone: Optional[str],
        keyword: Optional[str],
    ) -> Query:
        # 功能：根据院系、职称、姓名、邮箱、电话及关键字过滤教师列表。
        if department:
            query = query.filter(Teacher.dno == department)
        if title:
            query = query.filter(Teacher.title == title)
        if name:
            query = query.filter(Teacher.tname.ilike(f"%{name}%"))
        if email:
            query = query.filter(Teacher.email.ilike(f"%{email}%"))
        if phone:
            query = query.filter(Teacher.phone.ilike(f"%{phone}%"))
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(Teacher.tname.ilike(like), Teacher.email.ilike(like), Teacher.phone.ilike(like))
            )
        return query

    @classmethod
    def list(
        cls,
        *,
        department: Optional[str] = None,
        title: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Teacher], int]:
        # 功能：分页查询教师并返回总数。
        query = Teacher.query.options(selectinload(Teacher.department))
        query = cls._apply_filters(
            query,
            department=department,
            title=title,
            name=name,
            email=email,
            phone=phone,
            keyword=keyword,
        )
        total = query.count()
        items = (
            query.order_by(Teacher.tname)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def get(tno: str) -> Optional[Teacher]:
        # 功能：按工号加载单个教师。
        return db.session.get(Teacher, tno)

    @staticmethod
    def create(data: Dict[str, Any]) -> Teacher:
        # 功能：写入新教师记录。
        teacher = Teacher(**data)
        db.session.add(teacher)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return teacher

    @staticmethod
    def update(teacher: Teacher, data: Dict[str, Any]) -> Teacher:
        # 功能：更新教师字段并提交。
        for key, value in data.items():
            setattr(teacher, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return teacher

    @staticmethod
    def delete(teacher: Teacher) -> None:
        # 功能：删除教师记录。
        db.session.delete(teacher)
        db.session.commit()
