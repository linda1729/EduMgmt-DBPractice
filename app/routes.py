"""HTTP routes for the academic management system."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from .constants import (
    ENROLLMENT_STATUSES,
    ENTITY_PK_DUP_MSG,
    ENTITY_PK_EMPTY_MSG,
    GENDER_OPTIONS,
    REFERENTIAL_CLASSROOM_MSG,
    REFERENTIAL_COURSE_MSG,
    REFERENTIAL_DEPARTMENT_MSG,
    REFERENTIAL_STUDENT_COURSE_MSG,
    REFERENTIAL_TEACHER_MSG,
    REFERENTIAL_TERM_MSG,
    TEACHER_TITLES,
)
from .extensions import db
from .models import Classroom, Course, Department, Enrollment, Student, Teacher, Teaching, TermDict
from .services import (
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

bp = Blueprint("main", __name__)


def flash_integrity_error(detail: str) -> None:
    flash(format_integrity_violation(detail), "danger")


@bp.route("/")
def index() -> str:
    """Render the minimal front-end landing page."""
    # 功能：汇总系统关键指标与最新动态并渲染首页仪表盘。
    student_count = db.session.scalar(select(func.count()).select_from(Student)) or 0
    course_count = db.session.scalar(select(func.count()).select_from(Course)) or 0
    teacher_count = db.session.scalar(select(func.count()).select_from(Teacher)) or 0
    classroom_count = db.session.scalar(select(func.count()).select_from(Classroom)) or 0
    enrollment_count = db.session.scalar(select(func.count()).select_from(Enrollment)) or 0

    active_terms = (
        db.session.execute(
            select(TermDict.term_name).join(Teaching, Teaching.term == TermDict.term_code).distinct()
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
            .group_by(Course.cno)
            .order_by(func.count(Enrollment.sno).desc(), Course.cname)
            .limit(5)
        )
        .all()
    )

    top_course_chart = [
        {"label": row.cname, "value": int(row.enrolled_count or 0)}
        for row in top_courses
    ]

    # FIX: 不能把 ChunkedIteratorResult 直接喂给 dict(...)；先取行再组装
    rows = (
        db.session.execute(
            select(Enrollment.status, func.count().label("cnt"))
            .group_by(Enrollment.status)
            .order_by(Enrollment.status)
        )
        .all()
    )
    enrollment_status_summary = {status: int(cnt or 0) for status, cnt in rows}

    status_labels = list(enrollment_status_summary.keys())
    status_values = [int(enrollment_status_summary[label]) for label in status_labels]

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

    return render_template(
        "index.html",
        student_count=student_count,
        course_count=course_count,
        teacher_count=teacher_count,
        classroom_count=classroom_count,
        enrollment_count=enrollment_count,
        active_terms=active_terms,
        top_courses=top_courses,
        top_course_chart=top_course_chart,
        recent_enrollments=recent_enrollments,
        enrollment_status_summary=enrollment_status_summary,
        status_labels=status_labels,
        status_values=status_values,
    )


@bp.route("/students", methods=["GET", "POST"])
def manage_students() -> str:
    """List students and handle creation via simple form submission."""
    # 功能：展示学生概览与统计 dashboards，并处理创建学生的表单请求。
    departments = (
        db.session.execute(select(Department).order_by(Department.dname))
        .scalars()
        .all()
    )

    # 课程总体统计（学生页仪表盘）
    course_total = db.session.scalar(select(func.count()).select_from(Course)) or 0
    active_course_count = db.session.scalar(select(func.count()).where(Course.is_active)) or 0
    avg_credit = db.session.scalar(select(func.avg(Course.credits))) or 0

    dept_distribution_rows = (
        db.session.execute(
            select(Department.dname, func.count(Course.cno))
            .join(Course, Course.dno == Department.dno, isouter=True)
            .group_by(Department.dname)
            .order_by(Department.dname)
        )
        .all()
    )
    dept_distribution = [(dept or "未分配", count) for dept, count in dept_distribution_rows]

    student_total = db.session.scalar(select(func.count()).select_from(Student)) or 0

    # FIX: 不要 dict(ChunkedIteratorResult)；先 .all() 再 dict 推导
    gender_rows = (
        db.session.execute(
            select(Student.gender, func.count()).group_by(Student.gender)
        )
        .all()
    )
    gender_distribution = {gender: count for gender, count in gender_rows}

    dept_distribution_rows = (
        db.session.execute(
            select(Department.dname, func.count(Student.sno))
            .join(Student, Student.dno == Department.dno, isouter=True)
            .group_by(Department.dname)
            .order_by(Department.dname)
        )
        .all()
    )
    dept_distribution = [
        (dept or "未分配", count) for dept, count in dept_distribution_rows
    ]

    if request.method == "POST":
        form = request.form
        sno = form.get("sno", "").strip()
        sname = form.get("sname", "").strip()
        gender = form.get("gender", "").strip()
        enroll_year_raw = form.get("enroll_year", "").strip()
        birth_date_raw = form.get("birth_date", "").strip()
        dno = form.get("dno") or None
        email = form.get("email") or None
        phone = form.get("phone") or None

        existing_student = db.session.get(Student, sno) if sno else None

        if not sno:
            flash(ENTITY_PK_EMPTY_MSG, "danger")
        elif existing_student is not None:
            flash(ENTITY_PK_DUP_MSG, "danger")
        elif dno and db.session.get(Department, dno) is None:
            flash(REFERENTIAL_DEPARTMENT_MSG, "danger")
        elif not (sname and gender and enroll_year_raw.isdigit()):
            flash("请完整填写学号、姓名、性别和入学年份（数字）。", "danger")
        else:
            enroll_year = int(enroll_year_raw)
            violation = validate_student_enroll_year(enroll_year)
            if violation:
                flash_integrity_error(violation)
            elif gender not in GENDER_OPTIONS:
                flash("性别取值非法。", "danger")
            else:
                birth_date: datetime | None = None
                if birth_date_raw:
                    try:
                        birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d")
                    except ValueError:
                        flash("生日格式不正确，应为 YYYY-MM-DD。", "warning")
                        birth_date = None

                try:
                    student = Student(
                        sno=sno,
                        sname=sname,
                        gender=gender,
                        enroll_year=enroll_year,
                        birth_date=birth_date,
                        dno=dno or None,
                        email=email,
                        phone=phone,
                    )
                    db.session.add(student)
                    db.session.commit()
                    flash(f"学生 {sname} 创建成功。", "success")
                    return redirect(url_for("main.manage_students"))
                except IntegrityError as exc:
                    db.session.rollback()
                    flash(f"创建学生失败：{exc.orig}", "danger")

    sno_search = request.args.get("sno", "").strip()
    sname_search = request.args.get("name", "").strip()
    dept_filter = request.args.get("department", "").strip()

    student_query = (
        select(Student)
        .options(selectinload(Student.department))
        .order_by(Student.enroll_year.desc(), Student.sno)
    )

    if sno_search:
        pattern = f"%{sno_search}%"
        student_query = student_query.where(Student.sno.ilike(pattern))
    if sname_search:
        pattern = f"%{sname_search}%"
        student_query = student_query.where(Student.sname.ilike(f"%{sname_search}%"))

    if dept_filter:
        student_query = student_query.where(Student.dno == dept_filter)

    students = db.session.execute(student_query.limit(200)).scalars().all()

    return render_template(
        "students.html",
        students=students,
        departments=departments,
        gender_options=GENDER_OPTIONS,
        sno_search=sno_search,
        sname_search=sname_search,
        dept_filter=dept_filter,
        student_total=student_total,
        gender_distribution=gender_distribution,
        dept_distribution_labels=[label for label, _ in dept_distribution],
        dept_distribution_values=[value for _, value in dept_distribution],
    )


@bp.post("/students/<string:sno>/update")
def update_student(sno: str) -> str:
    """Handle student updates for email、电话等信息。"""
    # 功能：根据表单输入更新指定学生的联系方式、院系及基本属性。
    student = db.session.get(Student, sno)
    if student is None:
        flash("未找到指定学生。", "danger")
        return redirect(url_for("main.manage_students"))

    form = request.form
    student.sname = form.get("sname", student.sname).strip() or student.sname
    student.email = form.get("email") or None
    student.phone = form.get("phone") or None
    new_dno = form.get("dno") or None
    if new_dno:
        if db.session.get(Department, new_dno):
            student.dno = new_dno
        else:
            flash(REFERENTIAL_DEPARTMENT_MSG, "danger")
    else:
        student.dno = None
    gender = form.get("gender")
    if gender in GENDER_OPTIONS:
        student.gender = gender
    enroll_year_raw = form.get("enroll_year", "").strip()
    if enroll_year_raw:
        if enroll_year_raw.isdigit():
            enroll_year = int(enroll_year_raw)
            violation = validate_student_enroll_year(enroll_year)
            if violation:
                detail = violation.rstrip("。") + "，已保持原值。"
                flash_integrity_error(detail)
            else:
                student.enroll_year = enroll_year
        else:
            flash("入学年份需为数字，已保持原值。", "warning")
    birth_date_raw = form.get("birth_date", "").strip()
    if birth_date_raw:
        try:
            student.birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d")
        except ValueError:
            flash("生日格式不正确，应为 YYYY-MM-DD。", "warning")
    else:
        student.birth_date = None

    try:
        db.session.commit()
        flash(f"学生 {student.sname} 信息已更新。", "success")
    except IntegrityError as exc:
        db.session.rollback()
        flash(f"更新失败：{exc.orig}", "danger")

    return redirect(url_for("main.manage_students"))


@bp.post("/students/<string:sno>/delete")
def delete_student(sno: str) -> str:
    """删除学生及其关联选课。"""
    # 功能：移除学生及关联选课记录，保证界面与数据同步。
    student = db.session.get(Student, sno)
    if student is None:
        flash("未找到指定学生。", "danger")
    else:
        action = request.form.get("delete_action", "restrict")
        has_enrollments = bool(student.enrollments)

        def build_reference_detail() -> str:
            return describe_student_enrollment_reference(student)

        if has_enrollments and action == "restrict":
            flash_integrity_error(build_reference_detail())
            return redirect(url_for("main.manage_students"))
        if has_enrollments and action == "set_null":
            detail = build_reference_detail().rstrip("。") + "，无法通过置空解除引用。"
            flash_integrity_error(detail)
            return redirect(url_for("main.manage_students"))
        db.session.delete(student)
        try:
            db.session.commit()
            flash(f"学生 {student.sname} 已删除。", "info")
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"删除失败：{exc.orig}", "danger")
    return redirect(url_for("main.manage_students"))


@bp.route("/courses", methods=["GET", "POST"])
def manage_courses() -> str:
    """管理课程信息，包括创建、列表与筛选。"""
    # 功能：展示课程列表、支持筛选汇总并处理新增课程表单。
    departments = (
        db.session.execute(select(Department).order_by(Department.dname))
        .scalars()
        .all()
    )

    # FIX: 本函数内补齐统计变量，避免 NameError
    course_total = db.session.scalar(select(func.count()).select_from(Course)) or 0
    active_course_count = db.session.scalar(select(func.count()).where(Course.is_active)) or 0
    avg_credit = db.session.scalar(select(func.avg(Course.credits))) or 0

    dept_distribution_rows = (
        db.session.execute(
            select(Department.dname, func.count(Course.cno))
            .join(Course, Course.dno == Department.dno, isouter=True)
            .group_by(Department.dname)
            .order_by(Department.dname)
        )
        .all()
    )
    dept_distribution = [(dept or "未分配", count) for dept, count in dept_distribution_rows]

    if request.method == "POST":
        form = request.form
        cno = form.get("cno", "").strip()
        cname = form.get("cname", "").strip()
        credits_raw = form.get("credits", "").strip()
        hours_raw = form.get("hours", "").strip()
        dno_raw = form.get("dno")
        if isinstance(dno_raw, str):
            dno = dno_raw.strip() or None
        else:
            dno = None
        prereq_raw = form.get("prereq_cno")
        if isinstance(prereq_raw, str):
            prereq_cno = prereq_raw.strip() or None
        else:
            prereq_cno = None
        is_active_value = form.get("is_active", "true").lower()

        existing_course = db.session.get(Course, cno) if cno else None

        if not cno:
            flash(ENTITY_PK_EMPTY_MSG, "danger")
        elif existing_course is not None:
            flash(ENTITY_PK_DUP_MSG, "danger")
        elif dno and db.session.get(Department, dno) is None:
            flash(REFERENTIAL_DEPARTMENT_MSG, "danger")
        elif prereq_cno and db.session.get(Course, prereq_cno) is None:
            flash(REFERENTIAL_COURSE_MSG, "danger")
        elif not (cno and cname and credits_raw.isdigit() and hours_raw.isdigit()):
            flash("请完整填写课程号、名称、学分和学时。", "danger")
        elif prereq_cno and prereq_cno == cno:
            flash("先修课不能是课程自身。", "danger")
        else:
            credits = int(credits_raw)
            hours = int(hours_raw)
            violation = validate_course_credits(credits)
            if violation:
                flash_integrity_error(violation)
            else:
                violation = validate_course_hours(hours)
                if violation:
                    flash_integrity_error(violation)
                else:
                    is_active = is_active_value != "false"
                    try:
                        course = Course(
                            cno=cno,
                            cname=cname,
                            credits=credits,
                            hours=hours,
                            dno=dno,
                            prereq_cno=prereq_cno or None,
                            is_active=is_active,
                        )
                        db.session.add(course)
                        db.session.commit()
                        flash(f"课程 {cname} 创建成功。", "success")
                        return redirect(url_for("main.manage_courses"))
                    except IntegrityError as exc:
                        db.session.rollback()
                        flash(f"创建课程失败：{exc.orig}", "danger")

    course_code_search = request.args.get("cno", "").strip()
    course_name_search = request.args.get("name", "").strip()
    dept_filter = request.args.get("department", "").strip()

    course_query = (
        select(Course)
        .options(selectinload(Course.department), selectinload(Course.prerequisite))
        .order_by(Course.cno)
    )
    if course_code_search:
        course_query = course_query.where(Course.cno.ilike(f"%{course_code_search}%"))
    if course_name_search:
        course_query = course_query.where(Course.cname.ilike(f"%{course_name_search}%"))
    if dept_filter:
        course_query = course_query.where(Course.dno == dept_filter)

    courses = db.session.execute(course_query).scalars().all()
    all_courses = db.session.execute(select(Course).order_by(Course.cname)).scalars().all()

    return render_template(
        "courses.html",
        courses=courses,
        departments=departments,
        all_courses=all_courses,
        course_code_search=course_code_search,
        course_name_search=course_name_search,
        dept_filter=dept_filter,
        course_total=course_total,
        active_course_count=active_course_count,
        avg_credit=round(float(avg_credit), 2) if avg_credit else 0,
        course_dept_labels=[label for label, _ in dept_distribution],
        course_dept_values=[value for _, value in dept_distribution],
    )


@bp.post("/courses/<string:cno>/update")
def update_course(cno: str) -> str:
    """更新课程基础信息。"""
    # 功能：根据管理表单调整课程的标题、学分、学时与所属院系。
    course = db.session.get(Course, cno)
    if course is None:
        flash("未找到指定课程。", "danger")
        return redirect(url_for("main.manage_courses"))

    form = request.form
    course.cname = form.get("cname", course.cname).strip() or course.cname
    credits_raw = form.get("credits", "").strip()
    hours_raw = form.get("hours", "").strip()
    if credits_raw:
        if credits_raw.isdigit():
            credits_value = int(credits_raw)
            violation = validate_course_credits(credits_value)
            if violation:
                detail = violation.rstrip("。") + "，已保持原值。"
                flash_integrity_error(detail)
            else:
                course.credits = credits_value
        else:
            flash("学分需为整数，已保留原值。", "warning")
    if hours_raw:
        if hours_raw.isdigit():
            hours_value = int(hours_raw)
            violation = validate_course_hours(hours_value)
            if violation:
                detail = violation.rstrip("。") + "，已保持原值。"
                flash_integrity_error(detail)
            else:
                course.hours = hours_value
        else:
            flash("学时需为整数，已保留原值。", "warning")
    new_dno = form.get("dno") or None
    if new_dno:
        if db.session.get(Department, new_dno):
            course.dno = new_dno
        else:
            flash(REFERENTIAL_DEPARTMENT_MSG, "danger")
    else:
        course.dno = None
    prereq_cno = form.get("prereq_cno") or None
    if prereq_cno and prereq_cno == cno:
        flash("先修课不能为自身，已忽略此次修改。", "warning")
    elif prereq_cno and db.session.get(Course, prereq_cno) is None:
        flash(REFERENTIAL_COURSE_MSG, "danger")
    else:
        course.prereq_cno = prereq_cno or None
    is_active_value = form.get("is_active", "true").lower()
    course.is_active = is_active_value != "false"

    try:
        db.session.commit()
        flash(f"课程 {cno} 信息已更新。", "success")
    except IntegrityError as exc:
        db.session.rollback()
        flash(f"更新失败：{exc.orig}", "danger")

    return redirect(url_for("main.manage_courses"))


@bp.post("/courses/<string:cno>/delete")
def delete_course(cno: str) -> str:
    """删除课程记录。"""
    # 功能：移除课程并同步刷新管理页面列表。
    course = db.session.get(Course, cno)
    if course is None:
        flash("未找到课程。", "danger")
    else:
        action = request.form.get("delete_action", "restrict")
        referencing_courses = (
            db.session.execute(select(Course).where(Course.prereq_cno == cno))
            .scalars()
            .all()
        )
        has_prereq_refs = bool(referencing_courses)
        has_enrollments = bool(course.enrollments)
        has_teachings = bool(course.teachings)
        has_refs = has_prereq_refs or has_enrollments or has_teachings

        def build_reference_detail() -> str:
            if has_enrollments:
                return describe_course_enrollment_reference(course)
            if has_teachings:
                return describe_course_teaching_reference(course)
            if has_prereq_refs:
                return describe_course_prerequisite_reference(course, referencing_courses)
            return "存在引用记录，暂无法删除。"

        if has_refs and action == "restrict":
            flash_integrity_error(build_reference_detail())
            return redirect(url_for("main.manage_courses"))

        if action == "set_null":
            if has_enrollments or has_teachings:
                detail = build_reference_detail().rstrip("。") + "，无法通过置空解除引用。"
                flash_integrity_error(detail)
                return redirect(url_for("main.manage_courses"))
            for ref_course in referencing_courses:
                ref_course.prereq_cno = None
        elif action == "cascade":
            for enrollment in list(course.enrollments):
                db.session.delete(enrollment)
            for teaching in list(course.teachings):
                db.session.delete(teaching)
            for ref_course in referencing_courses:
                ref_course.prereq_cno = None

        db.session.delete(course)
        try:
            db.session.commit()
            flash(f"课程 {cno} 已删除。", "info")
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"删除失败，可能存在关联数据：{exc.orig}", "danger")
    return redirect(url_for("main.manage_courses"))


@bp.route("/enrollments", methods=["GET", "POST"])
def manage_enrollments() -> str:
    """管理选课记录，包括创建、查询与筛选。"""
    # 功能：提供选课 CRUD 表单、统计图表与多条件查询过滤。
    students = db.session.execute(select(Student).order_by(Student.sno)).scalars().all()
    courses = db.session.execute(select(Course).order_by(Course.cno)).scalars().all()
    terms = db.session.execute(select(TermDict).order_by(TermDict.term_code)).scalars().all()
    valid_term_codes = {term.term_code for term in terms}
    enrollment_total = db.session.scalar(select(func.count()).select_from(Enrollment)) or 0
    status_distribution_rows = (
        db.session.execute(
            select(Enrollment.status, func.count())
            .group_by(Enrollment.status)
            .order_by(Enrollment.status)
        )
        .all()
    )
    status_distribution = [(status, count) for status, count in status_distribution_rows]
    status_distribution_map = dict(status_distribution)

    if request.method == "POST":
        form = request.form
        sno = form.get("sno", "").strip()
        cno = form.get("cno", "").strip()
        year_taken_raw = form.get("year_taken", "").strip()
        term = form.get("term", "").strip()
        grade_raw = form.get("grade", "").strip()
        status = form.get("status", ENROLLMENT_STATUSES[0])
        existing_enrollment = (
            db.session.execute(
                select(Enrollment).where(Enrollment.sno == sno, Enrollment.cno == cno)
            ).scalar_one_or_none()
            if sno and cno
            else None
        )

        if not sno or not cno:
            flash(ENTITY_PK_EMPTY_MSG, "danger")
        elif existing_enrollment is not None:
            flash(ENTITY_PK_DUP_MSG, "danger")
        elif db.session.get(Student, sno) is None or db.session.get(Course, cno) is None:
            flash(REFERENTIAL_STUDENT_COURSE_MSG, "danger")
        elif not (year_taken_raw.isdigit() and term):
            flash("请完整填写学生、课程、学年与学期。", "danger")
        elif term not in valid_term_codes:
            flash("学期取值非法。", "danger")
        else:
            year_taken = int(year_taken_raw)
            grade: Decimal | None = None
            if grade_raw:
                try:
                    grade = Decimal(grade_raw)
                except InvalidOperation:
                    flash("成绩格式不正确，已忽略。", "warning")
                    grade = None
            if status not in ENROLLMENT_STATUSES:
                status = ENROLLMENT_STATUSES[0]

            enrollment = Enrollment(
                sno=sno,
                cno=cno,
                year_taken=year_taken,
                term=term,
                grade=grade,
                status=status,
            )
            db.session.add(enrollment)
            try:
                db.session.commit()
                flash("选课记录创建成功。", "success")
                return redirect(url_for("main.manage_enrollments"))
            except IntegrityError as exc:
                db.session.rollback()
                flash(f"创建选课记录失败：{exc.orig}", "danger")

    student_filter = request.args.get("student", "").strip()
    course_filter = request.args.get("course", "").strip()
    status_filter = request.args.get("status", "").strip()

    enrollment_query = (
        select(Enrollment, Student, Course)
        .join(Student, Student.sno == Enrollment.sno)
        .join(Course, Course.cno == Enrollment.cno)
        .order_by(Enrollment.enroll_date.desc())
    )
    if student_filter:
        enrollment_query = enrollment_query.where(Enrollment.sno == student_filter)
    if course_filter:
        enrollment_query = enrollment_query.where(Enrollment.cno == course_filter)
    if status_filter and status_filter in ENROLLMENT_STATUSES:
        enrollment_query = enrollment_query.where(Enrollment.status == status_filter)

    enrollments = db.session.execute(enrollment_query.limit(300)).all()
    term_lookup = {term.term_code: term.term_name for term in terms}

    return render_template(
        "enrollments.html",
        enrollments=enrollments,
        students=students,
        courses=courses,
        terms=terms,
        term_lookup=term_lookup,
        statuses=ENROLLMENT_STATUSES,
        student_filter=student_filter,
        course_filter=course_filter,
        status_filter=status_filter,
        enrollment_total=enrollment_total,
        enrollment_status_labels=[label for label, _ in status_distribution],
        enrollment_status_values=[value for _, value in status_distribution],
        enrollment_status_map=status_distribution_map,
    )


@bp.post("/enrollments/<string:sno>/<string:cno>/update")
def update_enrollment(sno: str, cno: str) -> str:
    """更新选课信息（成绩、状态等）。"""
    # 功能：根据输入调整学生选课的学年、学期、成绩及状态。
    enrollment = (
        db.session.execute(
            select(Enrollment).where(Enrollment.sno == sno, Enrollment.cno == cno)
        ).scalar_one_or_none()
    )
    if enrollment is None:
        flash("未找到选课记录。", "danger")
        return redirect(url_for("main.manage_enrollments"))

    form = request.form
    year_taken_raw = form.get("year_taken", "").strip()
    if year_taken_raw:
        if year_taken_raw.isdigit():
            enrollment.year_taken = int(year_taken_raw)
        else:
            flash("学年需为数字，已保持原值。", "warning")
    term = form.get("term")
    if term and db.session.get(TermDict, term):
        enrollment.term = term
    grade_raw = form.get("grade", "").strip()
    if grade_raw:
        try:
            enrollment.grade = Decimal(grade_raw)
        except InvalidOperation:
            flash("成绩格式不正确，已保持原值。", "warning")
    else:
        enrollment.grade = None
    status = form.get("status")
    if status in ENROLLMENT_STATUSES:
        enrollment.status = status

    try:
        db.session.commit()
        flash("选课记录已更新。", "success")
    except IntegrityError as exc:
        db.session.rollback()
        flash(f"更新失败：{exc.orig}", "danger")

    return redirect(url_for("main.manage_enrollments"))


@bp.post("/enrollments/<string:sno>/<string:cno>/delete")
def delete_enrollment(sno: str, cno: str) -> str:
    """删除选课记录。"""
    # 功能：移除学生与课程的选课关联并提示最终结果。
    enrollment = (
        db.session.execute(
            select(Enrollment).where(Enrollment.sno == sno, Enrollment.cno == cno)
        ).scalar_one_or_none()
    )
    if enrollment is None:
        flash("未找到选课记录。", "danger")
    else:
        db.session.delete(enrollment)
        try:
            db.session.commit()
            flash("选课记录已删除。", "info")
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"删除失败：{exc.orig}", "danger")
    return redirect(url_for("main.manage_enrollments"))


@bp.route("/classrooms", methods=["GET", "POST"])
def manage_classrooms() -> str:
    """管理教室信息。"""
    # 功能：展示教室资源、楼栋统计并支持创建新教室。
    classroom_total = db.session.scalar(select(func.count()).select_from(Classroom)) or 0
    avg_capacity = db.session.scalar(select(func.avg(Classroom.capacity))) or 0
    building_distribution_rows = (
        db.session.execute(
            select(Classroom.building, func.count())
            .group_by(Classroom.building)
            .order_by(Classroom.building)
        )
        .all()
    )
    building_distribution = [(building, count) for building, count in building_distribution_rows]
    building_distribution_map = dict(building_distribution)
    if request.method == "POST":
        form = request.form
        room_id = form.get("room_id", "").strip()
        building = form.get("building", "").strip()
        room_no = form.get("room_no", "").strip()
        capacity_raw = form.get("capacity", "").strip()
        existing_classroom = db.session.get(Classroom, room_id) if room_id else None

        if not room_id:
            flash(ENTITY_PK_EMPTY_MSG, "danger")
        elif existing_classroom is not None:
            flash(ENTITY_PK_DUP_MSG, "danger")
        elif not (building and room_no and capacity_raw.isdigit()):
            flash("请完整填写教室编号、楼栋、房间号和容量。", "danger")
        else:
            capacity = int(capacity_raw)
            violation = validate_classroom_capacity(capacity)
            if violation:
                flash_integrity_error(violation)
            else:
                classroom = Classroom(
                    room_id=room_id,
                    building=building,
                    room_no=room_no,
                    capacity=capacity,
                )
                db.session.add(classroom)
                try:
                    db.session.commit()
                    flash(f"教室 {room_id} 创建成功。", "success")
                    return redirect(url_for("main.manage_classrooms"))
                except IntegrityError as exc:
                    db.session.rollback()
                    flash(f"创建教室失败：{exc.orig}", "danger")

    classrooms = (
        db.session.execute(
            select(Classroom).order_by(Classroom.building, Classroom.room_no)
        )
        .scalars()
        .all()
    )

    return render_template(
        "classrooms.html",
        classrooms=classrooms,
        classroom_total=classroom_total,
        avg_capacity=round(float(avg_capacity), 1) if avg_capacity else 0,
        classroom_building_labels=[label for label, _ in building_distribution],
        classroom_building_values=[value for _, value in building_distribution],
        classroom_building_map=building_distribution_map,
    )


@bp.post("/classrooms/<string:room_id>/update")
def update_classroom(room_id: str) -> str:
    """更新教室信息。"""
    # 功能：调整指定教室的楼栋、房间编号与容量字段。
    classroom = db.session.get(Classroom, room_id)
    if classroom is None:
        flash("未找到教室。", "danger")
        return redirect(url_for("main.manage_classrooms"))

    form = request.form
    classroom.building = form.get("building", classroom.building).strip() or classroom.building
    classroom.room_no = form.get("room_no", classroom.room_no).strip() or classroom.room_no
    capacity_raw = form.get("capacity", "").strip()
    if capacity_raw:
        if capacity_raw.isdigit():
            capacity = int(capacity_raw)
            violation = validate_classroom_capacity(capacity)
            if violation:
                detail = violation.rstrip("。") + "，已保持原值。"
                flash_integrity_error(detail)
            else:
                classroom.capacity = capacity
        else:
            flash("容量需为整数，已保持原值。", "warning")

    try:
        db.session.commit()
        flash(f"教室 {room_id} 信息已更新。", "success")
    except IntegrityError as exc:
        db.session.rollback()
        flash(f"更新失败：{exc.orig}", "danger")

    return redirect(url_for("main.manage_classrooms"))


@bp.post("/classrooms/<string:room_id>/delete")
def delete_classroom(room_id: str) -> str:
    """删除教室。"""
    # 功能：删除教室记录并在界面上提示是否成功。
    classroom = db.session.get(Classroom, room_id)
    if classroom is None:
        flash("未找到教室。", "danger")
    else:
        action = request.form.get("delete_action", "restrict")
        has_teachings = bool(classroom.teachings)
        def build_reference_detail() -> str:
            return describe_classroom_teaching_reference(classroom)
        if has_teachings and action == "restrict":
            flash_integrity_error(build_reference_detail())
            return redirect(url_for("main.manage_classrooms"))
        if has_teachings and action == "set_null":
            for teaching in classroom.teachings:
                teaching.room_id = None
        if action == "cascade":
            for teaching in list(classroom.teachings):
                db.session.delete(teaching)
        db.session.delete(classroom)
        try:
            db.session.commit()
            flash(f"教室 {room_id} 已删除。", "info")
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"删除失败：{exc.orig}", "danger")
    return redirect(url_for("main.manage_classrooms"))


@bp.route("/teachers", methods=["GET", "POST"])
def manage_teachers() -> str:
    """管理教师信息。"""
    # 功能：展示教师列表、统计职称分布并处理新增教师提交。
    departments = db.session.execute(select(Department).order_by(Department.dname)).scalars().all()
    teacher_total = db.session.scalar(select(func.count()).select_from(Teacher)) or 0
    title_distribution_rows = (
        db.session.execute(
            select(Teacher.title, func.count())
            .group_by(Teacher.title)
            .order_by(Teacher.title)
        )
        .all()
    )
    title_distribution = [(title, count) for title, count in title_distribution_rows]
    title_distribution_map = dict(title_distribution)
    if request.method == "POST":
        form = request.form
        tno = form.get("tno", "").strip()
        tname = form.get("tname", "").strip()
        title = form.get("title", "").strip()
        dno = form.get("dno") or None
        email = form.get("email") or None
        phone = form.get("phone") or None
        existing_teacher = db.session.get(Teacher, tno) if tno else None

        if not tno:
            flash(ENTITY_PK_EMPTY_MSG, "danger")
        elif existing_teacher is not None:
            flash(ENTITY_PK_DUP_MSG, "danger")
        elif dno and db.session.get(Department, dno) is None:
            flash(REFERENTIAL_DEPARTMENT_MSG, "danger")
        elif not (tname and title):
            flash("请完整填写工号、姓名和职称。", "danger")
        elif title not in TEACHER_TITLES:
            flash("职称取值非法。", "danger")
        else:
            teacher = Teacher(
                tno=tno,
                tname=tname,
                title=title,
                dno=dno,
                email=email,
                phone=phone,
            )
            db.session.add(teacher)
            try:
                db.session.commit()
                flash(f"教师 {tname} 创建成功。", "success")
                return redirect(url_for("main.manage_teachers"))
            except IntegrityError as exc:
                db.session.rollback()
                flash(f"创建教师失败：{exc.orig}", "danger")

    teachers = (
        db.session.execute(
            select(Teacher)
            .options(selectinload(Teacher.department))
            .order_by(Teacher.tname)
        )
        .scalars()
        .all()
    )

    return render_template(
        "teachers.html",
        teachers=teachers,
        departments=departments,
        teacher_titles=TEACHER_TITLES,
        teacher_total=teacher_total,
        teacher_title_labels=[label for label, _ in title_distribution],
        teacher_title_values=[value for _, value in title_distribution],
        teacher_title_map=title_distribution_map,
    )


@bp.post("/teachers/<string:tno>/update")
def update_teacher(tno: str) -> str:
    """更新教师信息。"""
    # 功能：修改教师的姓名、职称、所属院系及联系方式。
    teacher = db.session.get(Teacher, tno)
    if teacher is None:
        flash("未找到教师。", "danger")
        return redirect(url_for("main.manage_teachers"))

    form = request.form
    teacher.tname = form.get("tname", teacher.tname).strip() or teacher.tname
    title = form.get("title")
    if title in TEACHER_TITLES:
        teacher.title = title
    new_dno = form.get("dno") or None
    if new_dno:
        if db.session.get(Department, new_dno):
            teacher.dno = new_dno
        else:
            flash(REFERENTIAL_DEPARTMENT_MSG, "danger")
    else:
        teacher.dno = None
    teacher.email = form.get("email") or None
    teacher.phone = form.get("phone") or None

    try:
        db.session.commit()
        flash(f"教师 {tno} 信息已更新。", "success")
    except IntegrityError as exc:
        db.session.rollback()
        flash(f"更新失败：{exc.orig}", "danger")

    return redirect(url_for("main.manage_teachers"))


@bp.post("/teachers/<string:tno>/delete")
def delete_teacher(tno: str) -> str:
    """删除教师记录。"""
    # 功能：移除教师档案并向界面反馈执行状态。
    teacher = db.session.get(Teacher, tno)
    if teacher is None:
        flash("未找到教师。", "danger")
    else:
        action = request.form.get("delete_action", "restrict")
        has_teachings = bool(teacher.teachings)

        def build_reference_detail() -> str:
            return describe_teacher_teaching_reference(teacher)
        if has_teachings and action == "restrict":
            flash_integrity_error(build_reference_detail())
            return redirect(url_for("main.manage_teachers"))
        if has_teachings and action == "set_null":
            detail = build_reference_detail().rstrip("。") + "，无法通过置空解除引用。"
            flash_integrity_error(detail)
            return redirect(url_for("main.manage_teachers"))
        if action == "cascade":
            for teaching in list(teacher.teachings):
                db.session.delete(teaching)
        db.session.delete(teacher)
        try:
            db.session.commit()
            flash(f"教师 {tno} 已删除。", "info")
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"删除失败：{exc.orig}", "danger")
    return redirect(url_for("main.manage_teachers"))


@bp.route("/teachings", methods=["GET", "POST"])
def manage_teachings() -> str:
    """管理授课安排。"""
    # 功能：整合课程、教师、教室资源以维护授课安排并提供创建能力。
    courses = db.session.execute(select(Course).order_by(Course.cno)).scalars().all()
    teachers = db.session.execute(select(Teacher).order_by(Teacher.tname)).scalars().all()
    classrooms = db.session.execute(select(Classroom).order_by(Classroom.building, Classroom.room_no)).scalars().all()
    terms = db.session.execute(select(TermDict).order_by(TermDict.term_code)).scalars().all()
    term_lookup = {term.term_code: term.term_name for term in terms}
    teaching_total = db.session.scalar(select(func.count()).select_from(Teaching)) or 0
    avg_teaching_capacity = db.session.scalar(select(func.avg(Teaching.capacity))) or 0
    term_distribution_rows = (
        db.session.execute(
            select(Teaching.term, func.count())
            .group_by(Teaching.term)
            .order_by(Teaching.term)
        )
        .all()
    )
    term_distribution = [(term_lookup.get(term, term), count) for term, count in term_distribution_rows]
    term_distribution_map = dict(term_distribution)

    if request.method == "POST":
        form = request.form
        cno = form.get("cno", "").strip()
        tno = form.get("tno", "").strip()
        year_offered_raw = form.get("year_offered", "").strip()
        term = form.get("term", "").strip()
        room_id = form.get("room_id") or None
        capacity_raw = form.get("capacity", "").strip()
        start_date_raw = form.get("start_date", "").strip()
        end_date_raw = form.get("end_date", "").strip()

        if not (cno and tno and year_offered_raw.isdigit() and term):
            flash("请完整填写课程、教师、开课年份和学期。", "danger")
        elif term not in term_lookup:
            flash("学期取值非法。", "danger")
        elif db.session.get(Course, cno) is None:
            flash(REFERENTIAL_COURSE_MSG, "danger")
        elif db.session.get(Teacher, tno) is None:
            flash(REFERENTIAL_TEACHER_MSG, "danger")
        elif room_id and db.session.get(Classroom, room_id) is None:
            flash(REFERENTIAL_CLASSROOM_MSG, "danger")
        else:
            if capacity_raw and not capacity_raw.isdigit():
                flash("容量需为整数，已使用默认值 120。", "warning")
            capacity = int(capacity_raw) if capacity_raw.isdigit() else 120
            start_date = None
            end_date = None
            if start_date_raw:
                try:
                    start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
                except ValueError:
                    flash("开始日期格式不正确。", "warning")
            if end_date_raw:
                try:
                    end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
                except ValueError:
                    flash("结束日期格式不正确。", "warning")

            teaching = Teaching(
                cno=cno,
                tno=tno,
                year_offered=int(year_offered_raw),
                term=term,
                room_id=room_id or None,
                capacity=capacity,
                start_date=start_date,
                end_date=end_date,
            )
            db.session.add(teaching)
            try:
                db.session.commit()
                flash("授课安排创建成功。", "success")
                return redirect(url_for("main.manage_teachings"))
            except IntegrityError as exc:
                db.session.rollback()
                flash(f"创建授课安排失败：{exc.orig}", "danger")

    teachings = (
        db.session.execute(
            select(Teaching, Course, Teacher, Classroom)
            .join(Course, Course.cno == Teaching.cno)
            .join(Teacher, Teacher.tno == Teaching.tno)
            .join(Classroom, Classroom.room_id == Teaching.room_id, isouter=True)
            .order_by(Teaching.year_offered.desc(), Teaching.term.desc(), Course.cno)
        )
        .all()
    )

    return render_template(
        "teachings.html",
        teachings=teachings,
        courses=courses,
        teachers=teachers,
        classrooms=classrooms,
        terms=terms,
        term_lookup=term_lookup,
        teaching_total=teaching_total,
        avg_teaching_capacity=round(float(avg_teaching_capacity), 1) if avg_teaching_capacity else 0,
        teaching_term_labels=[label for label, _ in term_distribution],
        teaching_term_values=[value for _, value in term_distribution],
        teaching_term_map=term_distribution_map,
    )


@bp.post("/teachings/<int:teach_id>/update")
def update_teaching(teach_id: int) -> str:
    """更新授课安排信息。"""
    # 功能：调整授课记录关联的课程、教师、教室及时间等字段。
    teaching = db.session.get(Teaching, teach_id)
    if teaching is None:
        flash("未找到授课安排。", "danger")
        return redirect(url_for("main.manage_teachings"))

    form = request.form
    cno = form.get("cno")
    if cno:
        if db.session.get(Course, cno):
            teaching.cno = cno
        else:
            flash(REFERENTIAL_COURSE_MSG, "danger")
    tno = form.get("tno")
    if tno:
        if db.session.get(Teacher, tno):
            teaching.tno = tno
        else:
            flash(REFERENTIAL_TEACHER_MSG, "danger")
    year_offered_raw = form.get("year_offered", "").strip()
    if year_offered_raw:
        if year_offered_raw.isdigit():
            teaching.year_offered = int(year_offered_raw)
        else:
            flash("开课年份需为数字，已保持原值。", "warning")
    term = form.get("term")
    if term and db.session.get(TermDict, term):
        teaching.term = term
    room_id = form.get("room_id")
    if room_id:
        if db.session.get(Classroom, room_id):
            teaching.room_id = room_id
        else:
            flash(REFERENTIAL_CLASSROOM_MSG, "danger")
    else:
        teaching.room_id = None
    capacity_raw = form.get("capacity", "").strip()
    if capacity_raw:
        if capacity_raw.isdigit():
            teaching.capacity = int(capacity_raw)
        else:
            flash("容量需为整数，已保持原值。", "warning")
    start_date_raw = form.get("start_date", "").strip()
    if start_date_raw:
        try:
            teaching.start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("开始日期格式不正确，已保持原值。", "warning")
    else:
        teaching.start_date = None
    end_date_raw = form.get("end_date", "").strip()
    if end_date_raw:
        try:
            teaching.end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("结束日期格式不正确，已保持原值。", "warning")
    else:
        teaching.end_date = None

    try:
        db.session.commit()
        flash("授课安排已更新。", "success")
    except IntegrityError as exc:
        db.session.rollback()
        flash(f"更新失败：{exc.orig}", "danger")

    return redirect(url_for("main.manage_teachings"))


@bp.post("/teachings/<int:teach_id>/delete")
def delete_teaching(teach_id: int) -> str:
    """删除授课安排。"""
    # 功能：删除授课排程并提示是否成功提交到数据库。
    teaching = db.session.get(Teaching, teach_id)
    if teaching is None:
        flash("未找到授课安排。", "danger")
    else:
        db.session.delete(teaching)
        try:
            db.session.commit()
            flash("授课安排已删除。", "info")
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"删除失败：{exc.orig}", "danger")
    return redirect(url_for("main.manage_teachings"))


@bp.route("/health")
def healthcheck() -> tuple[dict[str, str], int]:
    """Simple health-check endpoint."""
    # 功能：提供供监控探活使用的简单 JSON 响应。
    return jsonify({"status": "ok", "message": "Student academic management system API ready."}), 200
