"""Shared constant values used across the application layers."""

from __future__ import annotations

# 学生性别枚举
GENDER_OPTIONS = ["Male", "Female", "Other"]

# 选课状态枚举
ENROLLMENT_STATUSES = ["enrolled", "completed", "dropped"]

# 教师职称枚举
TEACHER_TITLES = ["Professor", "Associate Professor", "Assistant Professor", "Lecturer"]

# 实体完整性提示
ENTITY_PK_EMPTY_MSG = "违反实体完整性约束，主码不能为空"
ENTITY_PK_DUP_MSG = "违反实体完整性约束，主码不能重复"

# 参照完整性提示
REFERENTIAL_STUDENT_COURSE_MSG = "不符合参照表完整性，不存在该学生或课程"
REFERENTIAL_DEPARTMENT_MSG = "不符合参照表完整性，不存在该院系"
REFERENTIAL_COURSE_MSG = "不符合参照表完整性，不存在该课程"
REFERENTIAL_TEACHER_MSG = "不符合参照表完整性，不存在该教师"
REFERENTIAL_CLASSROOM_MSG = "不符合参照表完整性，不存在该教室"
REFERENTIAL_TERM_MSG = "不符合参照表完整性，不存在该学期"
