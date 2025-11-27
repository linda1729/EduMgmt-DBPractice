"""Helpers for integrity constraint validation and messaging."""

from __future__ import annotations

from typing import Any, Iterable, Optional

INTEGRITY_VIOLATION_PREFIX = "操作不符合完整性约束"

STUDENT_ENROLL_YEAR_MIN = 1990
COURSE_CREDIT_MIN = 1
COURSE_CREDIT_MAX = 10
COURSE_HOUR_MIN = 8
COURSE_HOUR_MAX = 128
CLASSROOM_CAPACITY_MIN = 10
CLASSROOM_CAPACITY_MAX = 1000


def format_integrity_violation(detail: str) -> str:
    """Return the unified integrity violation message."""
    normalized = detail.strip()
    return (
        INTEGRITY_VIOLATION_PREFIX
        if not normalized
        else f"{INTEGRITY_VIOLATION_PREFIX}，{normalized}"
    )


def validate_student_enroll_year(enroll_year: int) -> Optional[str]:
    """Ensure student enroll year meets the custom constraint."""
    if enroll_year < STUDENT_ENROLL_YEAR_MIN:
        return f"学生入学年份不能小于 {STUDENT_ENROLL_YEAR_MIN}。"
    return None


def validate_course_credits(credits: int) -> Optional[str]:
    """Ensure course credits fall within the configured range."""
    if not (COURSE_CREDIT_MIN <= credits <= COURSE_CREDIT_MAX):
        return f"学分需介于 {COURSE_CREDIT_MIN}-{COURSE_CREDIT_MAX}。"
    return None


def validate_course_hours(hours: int) -> Optional[str]:
    """Ensure course hours fall within the configured range."""
    if not (COURSE_HOUR_MIN <= hours <= COURSE_HOUR_MAX):
        return f"学时需介于 {COURSE_HOUR_MIN}-{COURSE_HOUR_MAX}。"
    return None


def validate_classroom_capacity(capacity: int) -> Optional[str]:
    """Ensure classroom capacity satisfies the custom constraint."""
    if not (CLASSROOM_CAPACITY_MIN <= capacity <= CLASSROOM_CAPACITY_MAX):
        return f"教室容量需介于 {CLASSROOM_CAPACITY_MIN}-{CLASSROOM_CAPACITY_MAX}。"
    return None


def _format_label(name: Optional[str], identifier: Optional[str], fallback: str) -> str:
    if name and identifier:
        return f"{name}（{identifier}）"
    return name or identifier or fallback


def _format_course_label(course: Any = None, *, cno: Optional[str] = None, name: Optional[str] = None) -> str:
    course_name = name or getattr(course, "cname", None)
    course_id = cno or getattr(course, "cno", None)
    return _format_label(course_name, course_id, "该课程")


def _format_student_label(student: Any = None, *, sno: Optional[str] = None, name: Optional[str] = None) -> str:
    student_name = name or getattr(student, "sname", None)
    student_id = sno or getattr(student, "sno", None)
    return _format_label(student_name, student_id, "该学生")


def _format_teacher_label(teacher: Any = None, *, tno: Optional[str] = None, name: Optional[str] = None) -> str:
    teacher_name = name or getattr(teacher, "tname", None)
    teacher_id = tno or getattr(teacher, "tno", None)
    return _format_label(teacher_name, teacher_id, "该教师")


def _format_term_label(year: Optional[int], term: Optional[str]) -> str:
    components = []
    if year is not None:
        components.append(f"{year} 学年")
    if term:
        components.append(f"{term} 学期")
    return " ".join(components) if components else "指定学期"


def _format_suffix(total: int, noun: str) -> str:
    if total <= 1:
        return ""
    return f"，另有 {total - 1} 条{noun}"


def describe_student_enrollment_reference(student: Any) -> str:
    """Return a descriptive detail that points to the course still referencing the student."""
    enrollments = list(getattr(student, "enrollments", []) or [])
    total = len(enrollments)
    if total == 0:
        return "存在选课记录引用该学生。"
    enrollment = enrollments[0]
    course_label = _format_course_label(enrollment.course, cno=getattr(enrollment, "cno", None))
    term_label = _format_term_label(getattr(enrollment, "year_taken", None), getattr(enrollment, "term", None))
    suffix = _format_suffix(total, "选课记录")
    student_label = _format_student_label(student)
    return f"课程 {course_label} 在 {term_label} 的选课记录仍包含学生 {student_label}{suffix}。"


def describe_course_enrollment_reference(course: Any) -> str:
    """Describe which student enrollment prevents deleting the course."""
    enrollments = list(getattr(course, "enrollments", []) or [])
    total = len(enrollments)
    if total == 0:
        return "存在学生选课记录引用该课程。"
    enrollment = enrollments[0]
    student_label = _format_student_label(enrollment.student, sno=getattr(enrollment, "sno", None))
    term_label = _format_term_label(getattr(enrollment, "year_taken", None), getattr(enrollment, "term", None))
    suffix = _format_suffix(total, "选课记录")
    course_label = _format_course_label(course)
    return f"学生 {student_label} 在 {term_label} 的选课记录仍指向课程 {course_label}{suffix}。"


def describe_teaching_reference(teaching: Any) -> str:
    """Return a detail sentence describing a teaching schedule still linked to the entity."""
    course_label = _format_course_label(teaching.course, cno=getattr(teaching, "cno", None))
    teacher_label = _format_teacher_label(teaching.teacher, tno=getattr(teaching, "tno", None))
    term_label = _format_term_label(getattr(teaching, "year_offered", None), getattr(teaching, "term", None))
    teach_id = getattr(teaching, "teach_id", "未知授课")
    return f"授课安排 {teach_id}（课程 {course_label}，教师 {teacher_label}，{term_label}）"


def describe_course_teaching_reference(course: Any) -> str:
    """Describe which teaching schedule keeps a course from being deleted."""
    teachings = list(getattr(course, "teachings", []) or [])
    total = len(teachings)
    if total == 0:
        return "仍有授课安排引用该课程。"
    teaching = teachings[0]
    suffix = _format_suffix(total, "授课安排")
    return f"{describe_teaching_reference(teaching)} 仍引用该课程{suffix}。"


def describe_teacher_teaching_reference(teacher: Any) -> str:
    """Describe which teaching schedule keeps a teacher from being deleted."""
    teachings = list(getattr(teacher, "teachings", []) or [])
    total = len(teachings)
    if total == 0:
        return "仍有授课安排引用该教师。"
    teaching = teachings[0]
    suffix = _format_suffix(total, "授课安排")
    teacher_label = _format_teacher_label(teacher)
    return f"{describe_teaching_reference(teaching)} 仍由教师 {teacher_label} 承担{suffix}。"


def describe_classroom_teaching_reference(classroom: Any) -> str:
    """Describe which teaching schedule keeps a classroom from being deleted."""
    teachings = list(getattr(classroom, "teachings", []) or [])
    total = len(teachings)
    if total == 0:
        return "仍有授课安排引用该教室。"
    teaching = teachings[0]
    suffix = _format_suffix(total, "授课安排")
    room_label = getattr(classroom, "room_id", "该教室")
    return f"{describe_teaching_reference(teaching)} 仍使用教室 {room_label}{suffix}。"


def describe_course_prerequisite_reference(
    course: Any, referencing_courses: Optional[Iterable[Any]] = None
) -> str:
    """Describe which advanced course still marks the given course as prerequisite."""
    refs = list(referencing_courses) if referencing_courses is not None else list(
        getattr(course, "advanced_courses", []) or []
    )
    total = len(refs)
    if total == 0:
        return "仍有课程将其设为先修课。"
    ref_course = refs[0]
    suffix = ""
    if total > 1:
        suffix = f"，另有 {total - 1} 门相关课程"
    target_label = _format_course_label(course)
    ref_label = _format_course_label(ref_course)
    return f"课程 {ref_label} 仍将 {target_label} 设为先修课{suffix}。"


__all__ = [
    "format_integrity_violation",
    "validate_student_enroll_year",
    "validate_course_credits",
    "validate_course_hours",
    "validate_classroom_capacity",
    "describe_student_enrollment_reference",
    "describe_course_enrollment_reference",
    "describe_course_teaching_reference",
    "describe_teacher_teaching_reference",
    "describe_classroom_teaching_reference",
    "describe_course_prerequisite_reference",
]
