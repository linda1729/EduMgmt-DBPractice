"""Service layer package."""

from .integrity import (
    describe_classroom_teaching_reference,
    describe_course_enrollment_reference,
    describe_course_prerequisite_reference,
    describe_course_teaching_reference,
    describe_student_enrollment_reference,
    describe_teacher_teaching_reference,
    format_integrity_violation,
    validate_classroom_capacity,
    validate_course_credits,
    validate_course_hours,
    validate_student_enroll_year,
)
from .seed_service import populate_sample_data

__all__ = [
    "describe_classroom_teaching_reference",
    "describe_course_enrollment_reference",
    "describe_course_prerequisite_reference",
    "describe_course_teaching_reference",
    "describe_student_enrollment_reference",
    "describe_teacher_teaching_reference",
    "format_integrity_violation",
    "validate_classroom_capacity",
    "validate_course_credits",
    "validate_course_hours",
    "validate_student_enroll_year",
    "populate_sample_data",
]
