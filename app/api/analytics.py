"""Analytics endpoints for dashboard data."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from sqlalchemy import func, select

from ..extensions import db
from ..models import Classroom, Course, Enrollment, Student, Teacher, Teaching, TermDict

bp = Blueprint("analytics_api", __name__)


def _count_rows(model) -> int:
    stmt = select(func.count()).select_from(model)
    return int(db.session.scalar(stmt) or 0)


@bp.get("/dashboard")
def dashboard_summary():
    """Return aggregated metrics used by the dashboard view."""
    student_count = _count_rows(Student)
    course_count = _count_rows(Course)
    teacher_count = _count_rows(Teacher)
    classroom_count = _count_rows(Classroom)
    enrollment_count = _count_rows(Enrollment)

    active_terms = (
        db.session.execute(
            select(TermDict.term_name)
            .join(Teaching, Teaching.term == TermDict.term_code)
            .distinct()
            .order_by(TermDict.term_name)
        )
        .scalars()
        .all()
    )

    top_courses = (
        db.session.execute(
            select(
                Course.cno,
                Course.cname,
                func.count(Enrollment.sno).label("enrolled_count"),
            )
            .join(Enrollment, Enrollment.cno == Course.cno, isouter=True)
            .group_by(Course.cno, Course.cname)
            .order_by(func.count(Enrollment.sno).desc(), Course.cname)
            .limit(5)
        )
        .all()
    )
    top_course_chart = {
        "labels": [row.cname for row in top_courses],
        "values": [int(row.enrolled_count or 0) for row in top_courses],
        "rows": [
            {
                "course_id": row.cno,
                "course_name": row.cname,
                "enrolled_count": int(row.enrolled_count or 0),
            }
            for row in top_courses
        ],
    }

    status_rows = (
        db.session.execute(
            select(Enrollment.status, func.count().label("cnt"))
            .group_by(Enrollment.status)
            .order_by(Enrollment.status)
        )
        .all()
    )
    status_chart = {
        "labels": [status for status, _ in status_rows],
        "values": [int(cnt or 0) for _, cnt in status_rows],
    }

    recent_enrollments = (
        db.session.execute(
            select(Enrollment, Student, Course)
            .join(Student, Student.sno == Enrollment.sno)
            .join(Course, Course.cno == Enrollment.cno)
            .order_by(Enrollment.enroll_date.desc())
            .limit(8)
        )
        .all()
    )
    recent_payload = [
        {
            "student_id": student.sno,
            "student_name": student.sname,
            "course_id": course.cno,
            "course_name": course.cname,
            "status": enrollment.status,
            "grade": float(enrollment.grade) if enrollment.grade is not None else None,
            "enroll_date": enrollment.enroll_date.isoformat() if enrollment.enroll_date else None,
        }
        for (enrollment, student, course) in recent_enrollments
    ]

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    current_year = now.year

    def _count_recent(model, column):
        if column is None:
            return 0
        stmt = select(func.count()).select_from(model).where(column >= thirty_days_ago)
        return int(db.session.scalar(stmt) or 0)

    enrollment_drop_count = int(
        db.session.scalar(
            select(func.count()).select_from(Enrollment).where(Enrollment.status == "dropped")
        )
        or 0
    )
    teaching_total = _count_rows(Teaching)
    teaching_with_room = int(
        db.session.scalar(
            select(func.count()).select_from(Teaching).where(Teaching.room_id.is_not(None))
        )
        or 0
    )
    course_reference_count = (
        enrollment_count
        + int(
            db.session.scalar(select(func.count()).select_from(Teaching).where(Teaching.cno.is_not(None)))
            or 0
        )
    )
    teacher_reference_count = int(
        db.session.scalar(select(func.count()).select_from(Teaching)) or 0
    )

    teaching_current_year = int(
        db.session.scalar(
            select(func.count()).select_from(Teaching).where(Teaching.year_offered >= current_year)
        )
        or 0
    )

    heatmap_rows = [
        {
            "table": "学生",
            "metrics": {
                "create": _count_recent(Student, Student.created_at) or student_count,
                "read": student_count,
                "update": _count_recent(Student, Student.updated_at),
                "delete": enrollment_count,
            },
        },
        {
            "table": "课程",
            "metrics": {
                "create": _count_recent(Course, Course.created_at) or course_count,
                "read": course_count,
                "update": _count_recent(Course, Course.updated_at),
                "delete": course_reference_count,
            },
        },
        {
            "table": "教师",
            "metrics": {
                "create": _count_recent(Teacher, Teacher.created_at) or teacher_count,
                "read": teacher_count,
                "update": _count_recent(Teacher, Teacher.updated_at),
                "delete": teacher_reference_count,
            },
        },
        {
            "table": "教室",
            "metrics": {
                "create": classroom_count,
                "read": classroom_count,
                "update": 0,
                "delete": teaching_with_room,
            },
        },
        {
            "table": "选课",
            "metrics": {
                "create": _count_recent(Enrollment, Enrollment.enroll_date) or enrollment_count,
                "read": enrollment_count,
                "update": _count_recent(Enrollment, Enrollment.updated_at),
                "delete": enrollment_drop_count,
            },
        },
        {
            "table": "授课安排",
            "metrics": {
                "create": teaching_current_year or teaching_total,
                "read": teaching_total,
                "update": 0,
                "delete": teaching_with_room,
            },
        },
    ]

    return jsonify(
        {
            "totals": {
                "students": student_count,
                "courses": course_count,
                "teachers": teacher_count,
                "classrooms": classroom_count,
                "enrollments": enrollment_count,
            },
            "active_terms": active_terms,
            "top_courses": top_course_chart,
            "status_chart": status_chart,
            "recent_enrollments": recent_payload,
            "crud_heatmap": heatmap_rows,
        }
    )
