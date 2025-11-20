"""Data access helpers for Student model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query

from ..extensions import db
from ..models import Student


class StudentRepository:
    """Encapsulate common Student queries."""

    @staticmethod
    def _apply_filters(
        query: Query,
        *,
        department: Optional[str],
        enroll_year: Optional[int],
        student_id: Optional[str],
        name: Optional[str],
        keyword: Optional[str],
    ) -> Query:
        # 功能：根据院系、入学年份、学号、姓名与关键字组合过滤学生查询。
        if department:
            query = query.filter(Student.dno == department)
        if enroll_year:
            query = query.filter(Student.enroll_year == enroll_year)
        if student_id:
            query = query.filter(Student.sno.ilike(f"%{student_id}%"))
        if name:
            query = query.filter(Student.sname.ilike(f"%{name}%"))
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(Student.sname.ilike(like), Student.email.ilike(like)))
        return query

    @classmethod
    def list(
        cls,
        *,
        department: Optional[str] = None,
        enroll_year: Optional[int] = None,
        student_id: Optional[str] = None,
        name: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Student], int]:
        # 功能：执行分页学生检索并返回结果集与总数。
        query = Student.query
        query = cls._apply_filters(
            query,
            department=department,
            enroll_year=enroll_year,
            student_id=student_id,
            name=name,
            keyword=keyword,
        )
        total = query.count()
        items = (
            query.order_by(Student.sno)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def get(sno: str) -> Optional[Student]:
        # 功能：按学号获取单个学生实例。
        return db.session.get(Student, sno)

    @staticmethod
    def create(data: Dict[str, Any]) -> Student:
        # 功能：创建学生记录并提交事务，若失败则回滚。
        student = Student(**data)
        db.session.add(student)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return student

    @staticmethod
    def update(student: Student, data: Dict[str, Any]) -> Student:
        # 功能：更新学生字段并提交数据库。
        for key, value in data.items():
            setattr(student, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return student

    @staticmethod
    def delete(student: Student) -> None:
        # 功能：删除学生并提交删除事务。
        db.session.delete(student)
        db.session.commit()
