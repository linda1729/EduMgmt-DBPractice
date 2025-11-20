"""SQLAlchemy ORM models mapping to the MySQL schema."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class TermDict(db.Model):
    __tablename__ = "TermDict"

    term_code: Mapped[str] = mapped_column("TermCode", db.String(10), primary_key=True)
    term_name: Mapped[str] = mapped_column("TermName", db.String(20), unique=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Term {self.term_code}>"


class Department(db.Model):
    __tablename__ = "Department"

    dno: Mapped[str] = mapped_column("Dno", db.String(6), primary_key=True)
    dname: Mapped[str] = mapped_column("Dname", db.String(100), unique=True, nullable=False)

    students: Mapped[list["Student"]] = relationship(back_populates="department", cascade="all")
    teachers: Mapped[list["Teacher"]] = relationship(back_populates="department", cascade="all")
    courses: Mapped[list["Course"]] = relationship(back_populates="department", cascade="all")

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Department {self.dno}>"


class Student(db.Model):
    __tablename__ = "Student"

    sno: Mapped[str] = mapped_column("Sno", db.String(12), primary_key=True)
    sname: Mapped[str] = mapped_column("Sname", db.String(50), nullable=False)
    gender: Mapped[str] = mapped_column(
        "Gender",
        db.Enum("Male", "Female", "Other", name="student_gender"),
        nullable=False,
    )
    birth_date: Mapped[Optional[datetime]] = mapped_column("BirthDate", db.Date, nullable=True)
    dno: Mapped[Optional[str]] = mapped_column(
        "Dno",
        db.String(6),
        ForeignKey("Department.Dno", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    enroll_year: Mapped[int] = mapped_column("EnrollYear", db.Integer, nullable=False)
    email: Mapped[Optional[str]] = mapped_column("Email", db.String(100), unique=True)
    phone: Mapped[Optional[str]] = mapped_column("Phone", db.String(20))
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt", db.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "UpdatedAt",
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    department: Mapped[Optional["Department"]] = relationship(back_populates="students")
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("EnrollYear >= 1990", name="ck_student_enroll_year"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Student {self.sno} {self.sname}>"


class Course(db.Model):
    __tablename__ = "Course"

    cno: Mapped[str] = mapped_column("Cno", db.String(10), primary_key=True)
    cname: Mapped[str] = mapped_column("Cname", db.String(100), nullable=False)
    credits: Mapped[int] = mapped_column("Credits", db.SmallInteger, nullable=False)
    hours: Mapped[int] = mapped_column("Hours", db.SmallInteger, nullable=False)
    dno: Mapped[Optional[str]] = mapped_column(
        "Dno",
        db.String(6),
        ForeignKey("Department.Dno", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    prereq_cno: Mapped[Optional[str]] = mapped_column(
        "PrereqCno",
        db.String(10),
        ForeignKey("Course.Cno", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column("IsActive", db.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt", db.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "UpdatedAt",
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    department: Mapped[Optional["Department"]] = relationship(back_populates="courses")
    prerequisite: Mapped[Optional["Course"]] = relationship(
        remote_side="Course.cno", backref="advanced_courses"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("Cname", "Dno", name="uq_course_name_dept"),
        CheckConstraint("Credits BETWEEN 1 AND 10", name="ck_course_credits"),
        CheckConstraint("Hours BETWEEN 8 AND 128", name="ck_course_hours"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Course {self.cno} {self.cname}>"


class Teacher(db.Model):
    __tablename__ = "Teacher"

    tno: Mapped[str] = mapped_column("Tno", db.String(10), primary_key=True)
    tname: Mapped[str] = mapped_column("Tname", db.String(50), nullable=False)
    title: Mapped[str] = mapped_column(
        "Title",
        db.Enum(
            "Professor",
            "Associate Professor",
            "Assistant Professor",
            "Lecturer",
            name="teacher_title",
        ),
        nullable=False,
    )
    dno: Mapped[Optional[str]] = mapped_column(
        "Dno",
        db.String(6),
        ForeignKey("Department.Dno", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column("Email", db.String(100), unique=True)
    phone: Mapped[Optional[str]] = mapped_column("Phone", db.String(20))
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt", db.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "UpdatedAt",
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    department: Mapped[Optional["Department"]] = relationship(back_populates="teachers")
    teachings: Mapped[list["Teaching"]] = relationship(back_populates="teacher")

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Teacher {self.tno} {self.tname}>"


class Classroom(db.Model):
    __tablename__ = "Classroom"

    room_id: Mapped[str] = mapped_column("RoomID", db.String(10), primary_key=True)
    building: Mapped[str] = mapped_column("Building", db.String(50), nullable=False)
    room_no: Mapped[str] = mapped_column("RoomNo", db.String(10), nullable=False)
    capacity: Mapped[int] = mapped_column("Capacity", db.SmallInteger, nullable=False)

    teachings: Mapped[list["Teaching"]] = relationship(back_populates="classroom")

    __table_args__ = (
        UniqueConstraint("Building", "RoomNo", name="uq_classroom_room"),
        CheckConstraint("Capacity BETWEEN 10 AND 1000", name="ck_classroom_capacity"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Classroom {self.room_id}>"


class Teaching(db.Model):
    __tablename__ = "Teaching"
    __table_args__ = {"sqlite_autoincrement": True}

    teach_id: Mapped[int] = mapped_column(
        "TeachID",
        db.BigInteger().with_variant(db.Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    cno: Mapped[str] = mapped_column(
        "Cno",
        db.String(10),
        ForeignKey("Course.Cno", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    tno: Mapped[str] = mapped_column(
        "Tno",
        db.String(10),
        ForeignKey("Teacher.Tno", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    year_offered: Mapped[int] = mapped_column("YearOffered", db.Integer, nullable=False)
    term: Mapped[str] = mapped_column(
        "Term",
        db.String(10),
        ForeignKey("TermDict.TermCode", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    room_id: Mapped[Optional[str]] = mapped_column(
        "RoomID",
        db.String(10),
        ForeignKey("Classroom.RoomID", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    capacity: Mapped[int] = mapped_column("Capacity", db.SmallInteger, nullable=False, default=120)
    start_date: Mapped[Optional[datetime]] = mapped_column("StartDate", db.Date)
    end_date: Mapped[Optional[datetime]] = mapped_column("EndDate", db.Date)

    course: Mapped["Course"] = relationship(back_populates="teachings")
    teacher: Mapped["Teacher"] = relationship(back_populates="teachings")
    classroom: Mapped[Optional["Classroom"]] = relationship(back_populates="teachings")

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Teaching {self.teach_id} {self.cno}>"


# Establish back-reference after Teaching definition to avoid circular reference ordering issues
Course.teachings = relationship("Teaching", back_populates="course")


class Enrollment(db.Model):
    __tablename__ = "SC"

    sno: Mapped[str] = mapped_column(
        "Sno",
        db.String(12),
        ForeignKey("Student.Sno", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    cno: Mapped[str] = mapped_column(
        "Cno",
        db.String(10),
        ForeignKey("Course.Cno", onupdate="CASCADE", ondelete="RESTRICT"),
        primary_key=True,
    )
    year_taken: Mapped[int] = mapped_column("YearTaken", db.Integer, nullable=False)
    term: Mapped[str] = mapped_column(
        "Term",
        db.String(10),
        ForeignKey("TermDict.TermCode", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    grade: Mapped[Optional[Decimal]] = mapped_column("Grade", db.Numeric(5, 2))
    status: Mapped[str] = mapped_column(
        "Status",
        db.Enum("enrolled", "dropped", "completed", name="sc_status"),
        nullable=False,
        default="enrolled",
    )
    enroll_date: Mapped[datetime] = mapped_column(
        "EnrollDate", db.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "UpdatedAt",
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")
    term_ref: Mapped["TermDict"] = relationship()

    __table_args__ = (
        CheckConstraint("(Grade IS NULL) OR (Grade >= 0 AND Grade <= 100)", name="ck_sc_grade"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Enrollment {self.sno}-{self.cno}>"


class GradeScale(db.Model):
    __tablename__ = "GradeScale"

    min_score: Mapped[Decimal] = mapped_column("MinScore", db.Numeric(5, 2), primary_key=True)
    max_score: Mapped[Decimal] = mapped_column("MaxScore", db.Numeric(5, 2), nullable=False)
    letter: Mapped[str] = mapped_column("Letter", db.String(2), nullable=False)
    point: Mapped[Decimal] = mapped_column("Point", db.Numeric(3, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("MinScore <= MaxScore", name="ck_gradescale_range"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<GradeScale {self.letter}>"


class CourseAggDaily(db.Model):
    __tablename__ = "CourseAggDaily"

    stat_date: Mapped[datetime] = mapped_column("StatDate", db.Date, primary_key=True)
    cno: Mapped[str] = mapped_column(
        "Cno",
        db.String(10),
        ForeignKey("Course.Cno", ondelete="CASCADE"),
        primary_key=True,
    )
    taken_count: Mapped[int] = mapped_column("TakenCount", db.Integer, nullable=False)
    avg_score: Mapped[Optional[Decimal]] = mapped_column("AvgScore", db.Numeric(6, 2))
    std_dev_score: Mapped[Optional[Decimal]] = mapped_column("StdDevScore", db.Numeric(6, 2))
    pass_rate: Mapped[Optional[Decimal]] = mapped_column("PassRate", db.Numeric(6, 4))

    course: Mapped["Course"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<CourseAggDaily {self.stat_date} {self.cno}>"
