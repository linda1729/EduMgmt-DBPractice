"""Data access helpers for Enrollment (SC) model."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query

from ..extensions import db
from ..models import Course, Enrollment


class EnrollmentRepository:
    """Encapsulate enrollment CRUD and helper queries."""

    @staticmethod
    def _apply_filters(query: Query, *, student_id: Optional[str], course_id: Optional[str], status: Optional[str], year: Optional[int], term: Optional[str]) -> Query:
        # 功能：增加学生、课程、状态、学年与学期的动态过滤条件。
        if student_id:
            query = query.filter(Enrollment.sno == student_id)
        if course_id:
            query = query.filter(Enrollment.cno == course_id)
        if status:
            query = query.filter(Enrollment.status == status)
        if year:
            query = query.filter(Enrollment.year_taken == year)
        if term:
            query = query.filter(Enrollment.term == term)
        return query

    @classmethod
    def list(cls, *, student_id: Optional[str] = None, course_id: Optional[str] = None, status: Optional[str] = None, year: Optional[int] = None, term: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Enrollment], int]:
        # 功能：分页查询选课记录并按时间排序。
        query = Enrollment.query
        query = cls._apply_filters(query, student_id=student_id, course_id=course_id, status=status, year=year, term=term)
        total = query.count()
        items = (
            query.order_by(Enrollment.enroll_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def get(sno: str, cno: str) -> Optional[Enrollment]:
        # 功能：获取指定学生-课程组合的唯一选课记录。
        return (
            Enrollment.query.filter(
                and_(Enrollment.sno == sno, Enrollment.cno == cno)
            )
            .limit(1)
            .one_or_none()
        )

    @staticmethod
    def exists(sno: str, cno: str) -> bool:
        # 功能：判断学生是否已选过某课程，避免重复插入。
        stmt = db.select(Enrollment).where(
            and_(Enrollment.sno == sno, Enrollment.cno == cno)
        )
        return db.session.execute(stmt).first() is not None

    @staticmethod
    def prerequisite_satisfied(sno: str, course: Course) -> bool:
        """Return True if the student has met prerequisite for the course."""
        # 功能：校验学生是否满足课程的先修要求。
        if not course.prereq_cno:
            return True
        prereq = db.session.get(Course, course.prereq_cno)
        if prereq is None:
            return True
        stmt = db.select(Enrollment).where(
            and_(
                Enrollment.sno == sno,
                Enrollment.cno == prereq.cno,
                Enrollment.status == "completed",
                Enrollment.grade.is_not(None),
                Enrollment.grade >= Decimal("60"),
            )
        )
        return db.session.execute(stmt).first() is not None

    @staticmethod
    def create(data: Dict[str, Any]) -> Enrollment:
        # 功能：创建选课记录并处理潜在数据库异常。
        enrollment = Enrollment(**data)
        db.session.add(enrollment)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return enrollment

    @staticmethod
    def update(enrollment: Enrollment, data: Dict[str, Any]) -> Enrollment:
        # 功能：更新选课成绩、状态等字段并提交。
        for key, value in data.items():
            setattr(enrollment, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return enrollment

    @staticmethod
    def delete(enrollment: Enrollment) -> None:
        # 功能：删除选课记录并落库。
        db.session.delete(enrollment)
        db.session.commit()
