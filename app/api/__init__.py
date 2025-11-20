"""API blueprint registration."""

from __future__ import annotations

from flask import Flask


def register_api(app: Flask) -> None:
    """Register versioned API blueprints."""
    # 功能：装载 v1 学生、课程与选课 API 蓝图并挂载到应用。
    from .analytics import bp as analytics_bp
    from .classrooms import bp as classrooms_bp
    from .teachers import bp as teachers_bp
    from .teachings import bp as teachings_bp
    from .students import bp as students_bp
    from .courses import bp as courses_bp
    from .enrollments import bp as enrollments_bp

    app.register_blueprint(analytics_bp, url_prefix="/api/v1/analytics")
    app.register_blueprint(students_bp, url_prefix="/api/v1/students")
    app.register_blueprint(courses_bp, url_prefix="/api/v1/courses")
    app.register_blueprint(enrollments_bp, url_prefix="/api/v1/enrollments")
    app.register_blueprint(teachers_bp, url_prefix="/api/v1/teachers")
    app.register_blueprint(classrooms_bp, url_prefix="/api/v1/classrooms")
    app.register_blueprint(teachings_bp, url_prefix="/api/v1/teachings")
