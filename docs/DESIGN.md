我现在需要做一个实验，实验要求用MySQL实现数据存储、查询、更新、删除等，并基于所设计的数据库实现一个“学生教务管理系统”。 设计教务系统数据库中的数据表，至少包括学生表Student（主键Sno）、课程表Course（主键Cno，要求包含“先修课”属性）和选课表SC（主键Sno,Cno，还要求包含“成绩”属性），用SQL语句建立学生教务数据库，并对每张表录入实验数据。  使用Python Flask，基于所设计的数据库，实现一个“学生教务管理系统”，应包括对数据库中数据的查询、添加、删除、修改等功能，界面友好。B/S或C/S架构不限。

# 1) 建库与通用设置

```sql
-- 建库并选择
CREATE DATABASE IF NOT EXISTS edu_mgmt
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE edu_mgmt;

-- 为了让 CHECK 真正生效，需 MySQL 8.0.16+（8.0.34+更稳）
SET sql_mode = 'STRICT_ALL_TABLES';
```

------

# 2) 参照/字典表（可选但强烈推荐）

```sql
-- 学期字典
CREATE TABLE TermDict (
  TermCode  VARCHAR(10) PRIMARY KEY,         -- 'Spring'/'Summer'/'Fall'/'Winter'
  TermName  VARCHAR(20) NOT NULL UNIQUE
);

INSERT INTO TermDict (TermCode, TermName) VALUES
('Spring','Spring'),('Summer','Summer'),('Fall','Fall'),('Winter','Winter');

-- 院系
CREATE TABLE Department (
  Dno      VARCHAR(6) PRIMARY KEY,           -- e.g. 'CS','MATH'
  Dname    VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO Department (Dno, Dname) VALUES
('CS','Computer Science'),
('MATH','Mathematics'),
('ENG','English');
```

------

# 3) 核心三表（含先修课）

## 3.1 学生表 `Student`

```sql
CREATE TABLE Student (
  Sno        VARCHAR(12) PRIMARY KEY,                     -- 学号
  Sname      VARCHAR(50) NOT NULL,
  Gender     ENUM('Male','Female','Other') NOT NULL,
  BirthDate  DATE,
  Dno        VARCHAR(6),                                  -- 所在院系
  EnrollYear YEAR NOT NULL,
  Email      VARCHAR(100) UNIQUE,
  Phone      VARCHAR(20),
  CHECK (EnrollYear >= 1990),
  CONSTRAINT fk_student_dept FOREIGN KEY (Dno)
    REFERENCES Department(Dno)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

-- 示例数据
INSERT INTO Student (Sno,Sname,Gender,BirthDate,Dno,EnrollYear,Email,Phone) VALUES
('20250001','Alice Wang','Female','2006-03-12','CS',  2025,'alice@uni.edu','+1-555-1001'),
('20250002','Bob Li','Male','2005-11-02','CS',         2025,'bob@uni.edu','+1-555-1002'),
('20240010','Chen Yu','Other','2004-08-30','MATH',     2024,'chen@uni.edu','+1-555-1010');
```

## 3.2 课程表 `Course`（**先修课单列 `PrereqCno`**）

> 按你的要求，把**先修课作为课程表中的单列**，并做**自引用外键**，删除先修课时，子课先修设为 NULL。

```sql
CREATE TABLE Course (
  Cno         VARCHAR(10) PRIMARY KEY,                   -- 课程号
  Cname       VARCHAR(100) NOT NULL,
  Credits     TINYINT UNSIGNED NOT NULL,                 -- 学分
  Hours       TINYINT UNSIGNED NOT NULL,                 -- 学时
  Dno         VARCHAR(6),                                -- 开课院系
  PrereqCno   VARCHAR(10) NULL,                          -- 先修课（单列）
  IsActive    BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (Cname, Dno),
  CHECK (Credits BETWEEN 1 AND 10),
  CHECK (Hours BETWEEN 8 AND 128),
  CONSTRAINT fk_course_dept FOREIGN KEY (Dno)
    REFERENCES Department(Dno)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT fk_course_prereq FOREIGN KEY (PrereqCno)
    REFERENCES Course(Cno)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

-- 示例数据（注意先插入无先修课的，再插入有先修课的）
INSERT INTO Course (Cno,Cname,Credits,Hours,Dno,PrereqCno,IsActive) VALUES
('CS101','Intro to Programming',3,48,'CS',NULL,TRUE),
('MATH101','Calculus I',4,64,'MATH',NULL,TRUE),
('CS102','Data Structures',3,48,'CS','CS101',TRUE),     -- 先修：CS101
('CS201','Algorithms',3,48,'CS','CS102',TRUE),          -- 先修：CS102
('ENG101','Academic Writing',2,32,'ENG',NULL,TRUE);
```

## 3.3 选课表 `SC`（**主键是 (Sno, Cno)**，含成绩）

> 按要求：`SC` 的**主键就是 (Sno, Cno)**。我额外加了学年/学期作为普通列，便于查询（但不纳入主键），这样一个学生**同一门课仅能选修一次**（若需重修，可在系统层加“撤选后再选”的业务流程或改表设计）。

```sql
CREATE TABLE SC (
  Sno         VARCHAR(12) NOT NULL,
  Cno         VARCHAR(10) NOT NULL,
  YearTaken   YEAR NOT NULL,
  Term        VARCHAR(10) NOT NULL,                      -- 参照 TermDict.TermCode
  Grade       DECIMAL(5,2) NULL,                         -- 成绩（0~100；未出分可空）
  Status      ENUM('enrolled','dropped','completed') NOT NULL DEFAULT 'enrolled',
  EnrollDate  DATETIME NOT NULL DEFAULT NOW(),
  PRIMARY KEY (Sno, Cno),
  CONSTRAINT fk_sc_student FOREIGN KEY (Sno)
    REFERENCES Student(Sno)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_sc_course FOREIGN KEY (Cno)
    REFERENCES Course(Cno)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_sc_term FOREIGN KEY (Term)
    REFERENCES TermDict(TermCode)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CHECK (Grade IS NULL OR (Grade >= 0 AND Grade <= 100))
);

-- 示例选课数据
INSERT INTO SC (Sno,Cno,YearTaken,Term,Grade,Status) VALUES
('20250001','CS101',2025,'Fall',NULL,'enrolled'),
('20250002','CS101',2025,'Fall',88.0,'completed'),
('20240010','MATH101',2024,'Fall',92.5,'completed'),
('20250002','ENG101',2025,'Fall',NULL,'enrolled');
```

------

# 4) 教师/授课/教室（完善系统所需）

## 4.1 教师表 `Teacher`

```sql
CREATE TABLE Teacher (
  Tno       VARCHAR(10) PRIMARY KEY,
  Tname     VARCHAR(50) NOT NULL,
  Title     ENUM('Professor','Associate Professor','Assistant Professor','Lecturer') NOT NULL,
  Dno       VARCHAR(6),
  Email     VARCHAR(100) UNIQUE,
  Phone     VARCHAR(20),
  CONSTRAINT fk_teacher_dept FOREIGN KEY (Dno)
    REFERENCES Department(Dno)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

INSERT INTO Teacher (Tno,Tname,Title,Dno,Email,Phone) VALUES
('T001','Dr. Smith','Professor','CS','smith@uni.edu','+1-555-2001'),
('T002','Dr. Brown','Associate Professor','MATH','brown@uni.edu','+1-555-2002'),
('T003','Ms. Davis','Lecturer','ENG','davis@uni.edu','+1-555-2003');
```

## 4.2 教室表 `Classroom`（可用于排课）

```sql
CREATE TABLE Classroom (
  RoomID     VARCHAR(10) PRIMARY KEY,        -- e.g. 'CS-101'
  Building   VARCHAR(50) NOT NULL,
  RoomNo     VARCHAR(10) NOT NULL,
  Capacity   SMALLINT UNSIGNED NOT NULL,
  UNIQUE (Building, RoomNo),
  CHECK (Capacity BETWEEN 10 AND 1000)
);

INSERT INTO Classroom (RoomID,Building,RoomNo,Capacity) VALUES
('CS-101','CS Building','101',120),
('MATH-201','Math Center','201',80);
```

## 4.3 授课安排 `Teaching`（哪个老师哪学期讲哪门课）

> `SC` 以 (Sno,Cno) 为主键，不包含场次/班号；若你之后想做“按班级/老师选课”，可把 `SC` 改为引用 `TeachID`。这里先给**授课表**方便查询展示。

```sql
CREATE TABLE Teaching (
  TeachID    BIGINT PRIMARY KEY AUTO_INCREMENT,
  Cno        VARCHAR(10) NOT NULL,
  Tno        VARCHAR(10) NOT NULL,
  YearOffered YEAR NOT NULL,
  Term       VARCHAR(10) NOT NULL,                       -- 参照 TermDict
  RoomID     VARCHAR(10),
  Capacity   SMALLINT UNSIGNED NOT NULL DEFAULT 120,
  StartDate  DATE NULL,
  EndDate    DATE NULL,
  CONSTRAINT fk_teaching_course FOREIGN KEY (Cno)
    REFERENCES Course(Cno)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_teaching_teacher FOREIGN KEY (Tno)
    REFERENCES Teacher(Tno)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_teaching_term FOREIGN KEY (Term)
    REFERENCES TermDict(TermCode)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_teaching_room FOREIGN KEY (RoomID)
    REFERENCES Classroom(RoomID)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

INSERT INTO Teaching (Cno,Tno,YearOffered,Term,RoomID,Capacity,StartDate,EndDate) VALUES
('CS101','T001',2025,'Fall','CS-101',120,'2025-09-01','2025-12-20'),
('CS102','T001',2026,'Spring','CS-101',100,'2026-02-15','2026-06-01'),
('MATH101','T002',2024,'Fall','MATH-201',80,'2024-09-01','2024-12-20'),
('ENG101','T003',2025,'Fall',NULL,80,'2025-09-01','2025-12-20');
```

------

# 5) 常用索引（提高查询性能）

```sql
-- 学生按院系/入学年常查
CREATE INDEX idx_student_dept ON Student(Dno);
CREATE INDEX idx_student_enrollyear ON Student(EnrollYear);

-- 课程按院系/先修课常查
CREATE INDEX idx_course_dept ON Course(Dno);
CREATE INDEX idx_course_prereq ON Course(PrereqCno);

-- 选课按学年学期、状态常查
CREATE INDEX idx_sc_term ON SC(YearTaken, Term);
CREATE INDEX idx_sc_status ON SC(Status);

-- 授课安排按学年学期、课程、教师常查
CREATE INDEX idx_teaching_time ON Teaching(YearOffered, Term);
CREATE INDEX idx_teaching_course ON Teaching(Cno);
CREATE INDEX idx_teaching_teacher ON Teaching(Tno);
```

------

# 6)先修课规则校验触发器

> 如果你希望**在选课时自动检查先修课是否通过**（例如成绩 ≥ 60），可以添加下面的触发器。
>  说明：当 `Course.PrereqCno` 不为空时，插入/更新 `SC` 会校验该学生是否**已在 `SC` 中修完先修课且成绩达标**。

```sql
DELIMITER $$

CREATE TRIGGER trg_sc_before_insert
BEFORE INSERT ON SC
FOR EACH ROW
BEGIN
  DECLARE v_prereq VARCHAR(10);
  DECLARE v_ok INT DEFAULT 0;

  SELECT PrereqCno INTO v_prereq
    FROM Course WHERE Cno = NEW.Cno;

  IF v_prereq IS NOT NULL THEN
    SELECT COUNT(*) INTO v_ok
      FROM SC
      WHERE Sno = NEW.Sno AND Cno = v_prereq
        AND Grade IS NOT NULL AND Grade >= 60
        AND Status IN ('completed');

    IF v_ok = 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Prerequisite not satisfied: student has not completed the prerequisite course with passing grade.';
    END IF;
  END IF;
END$$

CREATE TRIGGER trg_sc_before_update
BEFORE UPDATE ON SC
FOR EACH ROW
BEGIN
  -- 若更新的是 Cno，也做一次校验（一般业务不建议改 Cno）
  IF NEW.Cno <> OLD.Cno THEN
    DECLARE v_prereq2 VARCHAR(10);
    DECLARE v_ok2 INT DEFAULT 0;

    SELECT PrereqCno INTO v_prereq2
      FROM Course WHERE Cno = NEW.Cno;

    IF v_prereq2 IS NOT NULL THEN
      SELECT COUNT(*) INTO v_ok2
        FROM SC
        WHERE Sno = NEW.Sno AND Cno = v_prereq2
          AND Grade IS NOT NULL AND Grade >= 60
          AND Status IN ('completed');

      IF v_ok2 = 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Prerequisite not satisfied on update.';
      END IF;
    END IF;
  END IF;
END$$

DELIMITER ;
```

> 若你课程通过标准不是 60 分，可将触发器中的阈值改为你所在课程的“及格线”。

------

