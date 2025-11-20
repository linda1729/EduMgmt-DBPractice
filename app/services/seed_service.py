"""Seed service for generating demo data."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Set, Tuple

from sqlalchemy import and_

from ..extensions import db
from ..models import (
    Classroom,
    Course,
    CourseAggDaily,
    Department,
    Enrollment,
    Student,
    Teacher,
    TermDict,
    Teaching,
)

SEASON_META = {
    "SPR": ((3, 1), (6, 20)),
    "SUM": ((6, 21), (8, 31)),
    "FAL": ((9, 1), (12, 20)),
    "WIN": ((1, 5), (2, 28)),
}

GENDERS = ["Male", "Female", "Other"]
TITLES = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Lecturer",
]
def populate_sample_data(target_count: int = 100) -> None:
    """Populate each table with roughly ``target_count`` rows."""
    # 功能：协调调用各子方法，为所有核心表补齐约 target_count 条演示数据。
    random.seed(42)
    ensure_term_dict(target_count)
    ensure_departments(target_count)
    ensure_teachers(target_count)
    ensure_students(target_count)
    ensure_classrooms(target_count)
    ensure_courses(target_count)
    ensure_teachings(target_count)
    ensure_enrollments(target_count)
    ensure_course_agg_daily(target_count)


def ensure_term_dict(target_count: int) -> None:
    # 功能：根据目标数量生成学期字典，保证 term_dict 表足量。
    existing = TermDict.query.count()
    if existing >= target_count:
        return

    seasons = [
        ("SPR", "Spring"),
        ("SUM", "Summer"),
        ("FAL", "Fall"),
        ("WIN", "Winter"),
    ]
    existing_codes: Set[str] = {term.term_code for term in TermDict.query}

    year = 2020
    while len(existing_codes) < target_count:
        for suffix, label in seasons:
            code = f"{year}{suffix}"
            if code not in existing_codes:
                term = TermDict(term_code=code, term_name=f"{year} {label}")
                db.session.add(term)
                existing_codes.add(code)
                if len(existing_codes) >= target_count:
                    break
        year += 1
    db.session.commit()


def ensure_departments(target_count: int) -> None:
    # 功能：批量生成院系编号与名称，填满 departments 表。
    existing = Department.query.count()
    if existing >= target_count:
        return

    existing_codes: Set[str] = {dept.dno for dept in Department.query}
    idx = 1
    while len(existing_codes) < target_count:
        code = f"D{idx:03d}"
        if code not in existing_codes:
            department = Department(dno=code, dname=f"Department {idx:03d}")
            db.session.add(department)
            existing_codes.add(code)
        idx += 1
    db.session.commit()


def ensure_teachers(target_count: int) -> None:
    # 功能：随机分配院系、职称与联系方式，生成教师档案。
    existing = Teacher.query.count()
    if existing >= target_count:
        return

    departments = Department.query.all()
    if not departments:
        raise RuntimeError("No departments present when seeding teachers.")

    existing_ids: Set[str] = {teacher.tno for teacher in Teacher.query}
    idx = 1
    while len(existing_ids) < target_count:
        code = f"T{idx:04d}"
        if code not in existing_ids:
            dept = random.choice(departments)
            teacher = Teacher(
                tno=code,
                tname=f"Teacher {idx:04d}",
                title=random.choice(TITLES),
                dno=dept.dno,
                email=f"teacher{idx:04d}@example.edu",
                phone=f"+1-555-{2000 + idx:04d}",
            )
            db.session.add(teacher)
            existing_ids.add(code)
        idx += 1
    db.session.commit()


def ensure_students(target_count: int) -> None:
    # 功能：创建具备性别、生日、院系等信息的学生记录。
    existing = Student.query.count()
    if existing >= target_count:
        return

    departments = Department.query.all()
    if not departments:
        raise RuntimeError("No departments present when seeding students.")

    existing_ids: Set[str] = {student.sno for student in Student.query}
    idx = 1
    while len(existing_ids) < target_count:
        sno = f"{2020 + (idx % 6)}{idx:05d}"
        if sno not in existing_ids:
            enroll_year = 2019 + (idx % 7)
            birth_year = enroll_year - 12
            birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
            dept = random.choice(departments)
            student = Student(
                sno=sno,
                sname=f"Student {idx:05d}",
                gender=random.choice(GENDERS),
                birth_date=birth_date,
                dno=dept.dno,
                enroll_year=enroll_year,
                email=f"student{idx:05d}@example.edu",
                phone=f"+1-444-{1000 + idx:04d}",
            )
            db.session.add(student)
            existing_ids.add(sno)
        idx += 1
    db.session.commit()


def ensure_classrooms(target_count: int) -> None:
    # 功能：以递增编号构造教室楼栋、房间与容量。
    existing = Classroom.query.count()
    if existing >= target_count:
        return

    existing_ids: Set[str] = {room.room_id for room in Classroom.query}
    idx = 1
    while len(existing_ids) < target_count:
        room_id = f"RM{idx:03d}"
        if room_id not in existing_ids:
            building = f"Building {idx:03d}"
            room_no = f"{100 + idx}"
            classroom = Classroom(
                room_id=room_id,
                building=building,
                room_no=room_no,
                capacity=random.randint(40, 180),
            )
            db.session.add(classroom)
            existing_ids.add(room_id)
        idx += 1
    db.session.commit()


def ensure_courses(target_count: int) -> None:
    # 功能：随机生成课程、设置学分学时并构建先修关系。
    existing = Course.query.count()
    if existing >= target_count:
        return

    departments = Department.query.all()
    if not departments:
        raise RuntimeError("No departments present when seeding courses.")

    existing_codes: Set[str] = {course.cno for course in Course.query}
    base_course_codes: List[str] = [
        course.cno for course in Course.query.filter(Course.prereq_cno.is_(None)).all()
    ]
    base_target = max(20, target_count // 5)
    idx = 1
    while len(existing_codes) < target_count:
        code = f"C{idx:04d}"
        if code not in existing_codes:
            dept = random.choice(departments)
            credits = random.randint(2, 5)
            hours = credits * 16 + random.choice([0, 8, 16])
            if len(base_course_codes) < base_target:
                prereq = None
            else:
                prereq = random.choice(base_course_codes)
            course = Course(
                cno=code,
                cname=f"Course {idx:04d}",
                credits=credits,
                hours=hours,
                dno=dept.dno,
                prereq_cno=prereq,
                is_active=random.random() > 0.05,
            )
            db.session.add(course)
            existing_codes.add(code)
            if prereq is None:
                base_course_codes.append(code)
        idx += 1
    db.session.commit()


def ensure_teachings(target_count: int) -> None:
    # 功能：组合课程、教师、教室与学期生成授课排程。
    existing = Teaching.query.count()
    if existing >= target_count:
        return

    courses = Course.query.all()
    teachers = Teacher.query.all()
    classrooms = Classroom.query.all()
    terms = TermDict.query.all()
    if not (courses and teachers and classrooms and terms):
        raise RuntimeError("Missing required data when seeding teachings.")

    created = 0
    attempts = 0
    while existing + created < target_count and attempts < target_count * 4:
        course = random.choice(courses)
        teacher = random.choice(teachers)
        classroom = random.choice(classrooms)
        term = random.choice(terms)
        year = int(term.term_code[:4])
        suffix = term.term_code[4:]
        start_meta, end_meta = SEASON_META.get(suffix, ((3, 1), (6, 30)))
        start_month, start_day = start_meta
        end_month, end_day = end_meta

        start_date = date(year, start_month, min(start_day, 28))
        end_date = date(year, end_month, min(end_day, 28))

        teaching = Teaching(
            cno=course.cno,
            tno=teacher.tno,
            year_offered=year,
            term=term.term_code,
            room_id=classroom.room_id,
            capacity=random.randint(40, min(classroom.capacity, 200)),
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(teaching)
        created += 1
        attempts += 1

    db.session.commit()


def ensure_enrollments(target_count: int) -> None:
    # 功能：模拟学生选课过程，覆盖基础、进阶与进行中状态。
    existing = Enrollment.query.count()
    if existing >= target_count:
        return

    students = Student.query.all()
    courses = Course.query.all()
    terms = TermDict.query.all()
    if not (students and courses and terms):
        raise RuntimeError("Missing required data when seeding enrollments.")

    term_codes = [term.term_code for term in terms]
    base_courses = [course for course in courses if course.prereq_cno is None]
    advanced_courses = [course for course in courses if course.prereq_cno is not None]

    existing_pairs: Set[Tuple[str, str]] = {
        (enroll.sno, enroll.cno) for enroll in Enrollment.query.all()
    }
    completed_map: Dict[str, Set[str]] = {}
    for enroll in Enrollment.query.filter_by(status="completed").all():
        completed_map.setdefault(enroll.sno, set()).add(enroll.cno)

    created = 0
    for student in students:
        if existing + created >= target_count:
            break
        completed_set = completed_map.setdefault(student.sno, set())

        base_selection = random.sample(base_courses, k=min(2, len(base_courses)))
        for course in base_selection:
            pair = (student.sno, course.cno)
            if pair in existing_pairs:
                continue
            term_code = random.choice(term_codes)
            year = int(term_code[:4])
            enrollment = Enrollment(
                sno=student.sno,
                cno=course.cno,
                year_taken=year,
                term=term_code,
                status="completed",
                grade=Decimal(f"{random.uniform(70, 96):.2f}"),
            )
            db.session.add(enrollment)
            existing_pairs.add(pair)
            completed_set.add(course.cno)
            created += 1
            if existing + created >= target_count:
                break

        if existing + created >= target_count:
            break

    # Advanced courses for eligible students
    for course in advanced_courses:
        if existing + created >= target_count:
            break
        prereq = course.prereq_cno
        eligible_students = [
            student
            for student in students
            if prereq in completed_map.get(student.sno, set())
        ]
        if not eligible_students:
            continue
        sample_size = min(1, len(eligible_students))
        for student in random.sample(eligible_students, sample_size):
            pair = (student.sno, course.cno)
            if pair in existing_pairs:
                continue
            term_code = random.choice(term_codes)
            year = int(term_code[:4])
            status = random.choice(["enrolled", "completed"])
            grade = (
                Decimal(f"{random.uniform(72, 98):.2f}") if status == "completed" else None
            )
            enrollment = Enrollment(
                sno=student.sno,
                cno=course.cno,
                year_taken=year,
                term=term_code,
                status=status,
                grade=grade,
            )
            db.session.add(enrollment)
            existing_pairs.add(pair)
            if status == "completed" and grade is not None:
                completed_map.setdefault(student.sno, set()).add(course.cno)
            created += 1
            if existing + created >= target_count:
                break
        if existing + created >= target_count:
            break

    # Fill remaining slots with in-progress enrollments
    idx = 0
    while existing + created < target_count and idx < target_count * 4:
        student = random.choice(students)
        course = random.choice(courses)
        pair = (student.sno, course.cno)
        if pair in existing_pairs:
            idx += 1
            continue
        term_code = random.choice(term_codes)
        year = int(term_code[:4])
        status = random.choice(["enrolled", "dropped"])
        enrollment = Enrollment(
            sno=student.sno,
            cno=course.cno,
            year_taken=year,
            term=term_code,
            status=status,
            grade=None,
        )
        db.session.add(enrollment)
        existing_pairs.add(pair)
        created += 1
        idx += 1

    db.session.commit()


def ensure_course_agg_daily(target_count: int) -> None:
    # 功能：生成每日课程统计指标，模拟报表使用数据。
    existing = CourseAggDaily.query.count()
    if existing >= target_count:
        return

    courses = Course.query.limit(20).all()
    if not courses:
        return

    base_date = date.today() - timedelta(days=target_count)
    created = 0
    idx = 0
    while existing + created < target_count and idx < target_count * 2:
        course = courses[idx % len(courses)]
        stat_date = base_date + timedelta(days=idx)
        exists = CourseAggDaily.query.filter(
            and_(CourseAggDaily.stat_date == stat_date, CourseAggDaily.cno == course.cno)
        ).first()
        if exists:
            idx += 1
            continue
        taken_count = random.randint(30, 120)
        avg_score = Decimal(f"{random.uniform(70, 95):.2f}")
        std_dev = Decimal(f"{random.uniform(5, 15):.2f}")
        pass_rate = Decimal(f"{random.uniform(0.6, 0.95):.4f}")
        agg = CourseAggDaily(
            stat_date=stat_date,
            cno=course.cno,
            taken_count=taken_count,
            avg_score=avg_score,
            std_dev_score=std_dev,
            pass_rate=pass_rate,
        )
        db.session.add(agg)
        created += 1
        idx += 1

    db.session.commit()
