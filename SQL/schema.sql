-- schema.sql
-- 构建 edu_mgmt 数据库的全部结构、索引、视图与触发器

/*
 * 1. 数据库与全局设置
 */
CREATE DATABASE IF NOT EXISTS edu_mgmt
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE edu_mgmt;

-- 确保 CHECK 约束生效并保持严格模式
SET sql_mode = 'STRICT_ALL_TABLES';

/*
 * 2. 参照/字典表
 */
CREATE TABLE IF NOT EXISTS TermDict (
  TermCode VARCHAR(10) PRIMARY KEY COMMENT 'Spring/Summer/Fall/Winter',
  TermName VARCHAR(20) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Department (
  Dno   VARCHAR(6) PRIMARY KEY COMMENT '院系代码，如 CS/MATH',
  Dname VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO TermDict (TermCode, TermName) VALUES
('Spring','Spring'),
('Summer','Summer'),
('Fall','Fall'),
('Winter','Winter')
ON DUPLICATE KEY UPDATE TermName = VALUES(TermName);

INSERT INTO Department (Dno, Dname) VALUES
('CS','Computer Science'),
('MATH','Mathematics'),
('ENG','English')
ON DUPLICATE KEY UPDATE Dname = VALUES(Dname);

/*
 * 3. 核心实体表
 */
CREATE TABLE IF NOT EXISTS Student (
  Sno        VARCHAR(12) PRIMARY KEY COMMENT '学生学号',
  Sname      VARCHAR(50) NOT NULL,
  Gender     ENUM('Male','Female','Other') NOT NULL,
  BirthDate  DATE NULL,
  Dno        VARCHAR(6) NULL,
  EnrollYear YEAR NOT NULL,
  Email      VARCHAR(100) UNIQUE,
  Phone      VARCHAR(20),
  CreatedAt  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UpdatedAt  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CHECK (EnrollYear >= 1990),
  CONSTRAINT fk_student_dept FOREIGN KEY (Dno)
    REFERENCES Department(Dno)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Course (
  Cno         VARCHAR(10) PRIMARY KEY COMMENT '课程号',
  Cname       VARCHAR(100) NOT NULL,
  Credits     TINYINT UNSIGNED NOT NULL,
  Hours       TINYINT UNSIGNED NOT NULL,
  Dno         VARCHAR(6) NULL,
  PrereqCno   VARCHAR(10) NULL,
  IsActive    BOOLEAN NOT NULL DEFAULT TRUE,
  CreatedAt   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UpdatedAt   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_course_name_dept (Cname, Dno),
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
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Teacher (
  Tno       VARCHAR(10) PRIMARY KEY,
  Tname     VARCHAR(50) NOT NULL,
  Title     ENUM('Professor','Associate Professor','Assistant Professor','Lecturer') NOT NULL,
  Dno       VARCHAR(6) NULL,
  Email     VARCHAR(100) UNIQUE,
  Phone     VARCHAR(20),
  CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_teacher_dept FOREIGN KEY (Dno)
    REFERENCES Department(Dno)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Classroom (
  RoomID   VARCHAR(10) PRIMARY KEY COMMENT '如 CS-101',
  Building VARCHAR(50) NOT NULL,
  RoomNo   VARCHAR(10) NOT NULL,
  Capacity SMALLINT UNSIGNED NOT NULL,
  UNIQUE KEY uq_classroom_room (Building, RoomNo),
  CHECK (Capacity BETWEEN 10 AND 1000)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS SC (
  Sno         VARCHAR(12) NOT NULL,
  Cno         VARCHAR(10) NOT NULL,
  YearTaken   YEAR NOT NULL,
  Term        VARCHAR(10) NOT NULL,
  Grade       DECIMAL(5,2) NULL,
  Status      ENUM('enrolled','dropped','completed') NOT NULL DEFAULT 'enrolled',
  EnrollDate  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UpdatedAt   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Teaching (
  TeachID     BIGINT PRIMARY KEY AUTO_INCREMENT,
  Cno         VARCHAR(10) NOT NULL,
  Tno         VARCHAR(10) NOT NULL,
  YearOffered YEAR NOT NULL,
  Term        VARCHAR(10) NOT NULL,
  RoomID      VARCHAR(10) NULL,
  Capacity    SMALLINT UNSIGNED NOT NULL DEFAULT 120,
  StartDate   DATE NULL,
  EndDate     DATE NULL,
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
) ENGINE=InnoDB;

/*
 * 4. 评分相关表
 */
CREATE TABLE IF NOT EXISTS GradeScale (
  MinScore DECIMAL(5,2) NOT NULL,
  MaxScore DECIMAL(5,2) NOT NULL,
  Letter   VARCHAR(2)   NOT NULL,
  Point    DECIMAL(3,2) NOT NULL,
  CHECK (MinScore <= MaxScore)
) ENGINE=InnoDB;

DELETE FROM GradeScale;
INSERT INTO GradeScale (MinScore, MaxScore, Letter, Point) VALUES
(93,100,'A',4.0),(90,92.99,'A-',3.7),
(87,89.99,'B+',3.3),(83,86.99,'B',3.0),(80,82.99,'B-',2.7),
(77,79.99,'C+',2.3),(73,76.99,'C',2.0),(70,72.99,'C-',1.7),
(60,69.99,'D',1.0),(0,59.99,'F',0.0);

CREATE TABLE IF NOT EXISTS CourseAggDaily (
  StatDate    DATE NOT NULL,
  Cno         VARCHAR(10) NOT NULL,
  TakenCount  INT NOT NULL,
  AvgScore    DECIMAL(6,2) NULL,
  StdDevScore DECIMAL(6,2) NULL,
  PassRate    DECIMAL(6,4) NULL,
  PRIMARY KEY (StatDate, Cno),
  CONSTRAINT fk_courseagg_course FOREIGN KEY (Cno)
    REFERENCES Course(Cno)
    ON DELETE CASCADE
) ENGINE=InnoDB;

/*
 * 5. 初始示例数据
 */
INSERT INTO Student (Sno,Sname,Gender,BirthDate,Dno,EnrollYear,Email,Phone) VALUES
('20250001','Alice Wang','Female','2006-03-12','CS',2025,'alice@uni.edu','+1-555-1001'),
('20250002','Bob Li','Male','2005-11-02','CS',2025,'bob@uni.edu','+1-555-1002'),
('20240010','Chen Yu','Other','2004-08-30','MATH',2024,'chen@uni.edu','+1-555-1010')
ON DUPLICATE KEY UPDATE
  Sname = VALUES(Sname),
  Gender = VALUES(Gender),
  BirthDate = VALUES(BirthDate),
  Dno = VALUES(Dno),
  EnrollYear = VALUES(EnrollYear),
  Email = VALUES(Email),
  Phone = VALUES(Phone);

INSERT INTO Course (Cno,Cname,Credits,Hours,Dno,PrereqCno,IsActive) VALUES
('CS101','Intro to Programming',3,48,'CS',NULL,TRUE),
('MATH101','Calculus I',4,64,'MATH',NULL,TRUE),
('CS102','Data Structures',3,48,'CS','CS101',TRUE),
('CS201','Algorithms',3,48,'CS','CS102',TRUE),
('ENG101','Academic Writing',2,32,'ENG',NULL,TRUE)
ON DUPLICATE KEY UPDATE
  Cname = VALUES(Cname),
  Credits = VALUES(Credits),
  Hours = VALUES(Hours),
  Dno = VALUES(Dno),
  PrereqCno = VALUES(PrereqCno),
  IsActive = VALUES(IsActive);

INSERT INTO Teacher (Tno,Tname,Title,Dno,Email,Phone) VALUES
('T001','Dr. Smith','Professor','CS','smith@uni.edu','+1-555-2001'),
('T002','Dr. Brown','Associate Professor','MATH','brown@uni.edu','+1-555-2002'),
('T003','Ms. Davis','Lecturer','ENG','davis@uni.edu','+1-555-2003')
ON DUPLICATE KEY UPDATE
  Tname = VALUES(Tname),
  Title = VALUES(Title),
  Dno = VALUES(Dno),
  Email = VALUES(Email),
  Phone = VALUES(Phone);

INSERT INTO Classroom (RoomID,Building,RoomNo,Capacity) VALUES
('CS-101','CS Building','101',120),
('MATH-201','Math Center','201',80)
ON DUPLICATE KEY UPDATE
  Building = VALUES(Building),
  RoomNo = VALUES(RoomNo),
  Capacity = VALUES(Capacity);

INSERT INTO Teaching (TeachID,Cno,Tno,YearOffered,Term,RoomID,Capacity,StartDate,EndDate) VALUES
(1,'CS101','T001',2025,'Fall','CS-101',120,'2025-09-01','2025-12-20'),
(2,'CS102','T001',2026,'Spring','CS-101',100,'2026-02-15','2026-06-01'),
(3,'MATH101','T002',2024,'Fall','MATH-201',80,'2024-09-01','2024-12-20'),
(4,'ENG101','T003',2025,'Fall',NULL,80,'2025-09-01','2025-12-20')
ON DUPLICATE KEY UPDATE
  Cno = VALUES(Cno),
  Tno = VALUES(Tno),
  YearOffered = VALUES(YearOffered),
  Term = VALUES(Term),
  RoomID = VALUES(RoomID),
  Capacity = VALUES(Capacity),
  StartDate = VALUES(StartDate),
  EndDate = VALUES(EndDate);

INSERT INTO SC (Sno,Cno,YearTaken,Term,Grade,Status,EnrollDate) VALUES
('20250001','CS101',2025,'Fall',NULL,'enrolled',CURRENT_TIMESTAMP),
('20250002','CS101',2025,'Fall',88.0,'completed',CURRENT_TIMESTAMP),
('20240010','MATH101',2024,'Fall',92.5,'completed',CURRENT_TIMESTAMP),
('20250002','ENG101',2025,'Fall',NULL,'enrolled',CURRENT_TIMESTAMP)
ON DUPLICATE KEY UPDATE
  YearTaken = VALUES(YearTaken),
  Term = VALUES(Term),
  Grade = VALUES(Grade),
  Status = VALUES(Status),
  EnrollDate = VALUES(EnrollDate);

/*
 * 6. 索引（额外于主键/唯一约束）
 */
DROP INDEX IF EXISTS idx_student_dept ON Student;
CREATE INDEX idx_student_dept ON Student(Dno);
DROP INDEX IF EXISTS idx_student_enrollyear ON Student;
CREATE INDEX idx_student_enrollyear ON Student(EnrollYear);

DROP INDEX IF EXISTS idx_course_dept ON Course;
CREATE INDEX idx_course_dept ON Course(Dno);
DROP INDEX IF EXISTS idx_course_prereq ON Course;
CREATE INDEX idx_course_prereq ON Course(PrereqCno);
DROP INDEX IF EXISTS idx_course_dept_active ON Course;
CREATE INDEX idx_course_dept_active ON Course(Dno, IsActive);

DROP INDEX IF EXISTS idx_sc_term ON SC;
CREATE INDEX idx_sc_term ON SC(YearTaken, Term);
DROP INDEX IF EXISTS idx_sc_status ON SC;
CREATE INDEX idx_sc_status ON SC(Status);
DROP INDEX IF EXISTS idx_sc_student_term ON SC;
CREATE INDEX idx_sc_student_term ON SC(Sno, YearTaken, Term);
DROP INDEX IF EXISTS idx_sc_course_term ON SC;
CREATE INDEX idx_sc_course_term ON SC(Cno, YearTaken, Term);
DROP INDEX IF EXISTS idx_sc_grade ON SC;
CREATE INDEX idx_sc_grade ON SC(Grade);

DROP INDEX IF EXISTS idx_teaching_time ON Teaching;
CREATE INDEX idx_teaching_time ON Teaching(YearOffered, Term);
DROP INDEX IF EXISTS idx_teaching_course ON Teaching;
CREATE INDEX idx_teaching_course ON Teaching(Cno);
DROP INDEX IF EXISTS idx_teaching_teacher ON Teaching;
CREATE INDEX idx_teaching_teacher ON Teaching(Tno);
DROP INDEX IF EXISTS idx_teaching_dept_time ON Teaching;
CREATE INDEX idx_teaching_dept_time ON Teaching(YearOffered, Term, Cno, Tno);

/*
 * 7. 全文索引（用于多关键字检索）
 */
DROP INDEX IF EXISTS ft_student ON Student;
ALTER TABLE Student
  ADD FULLTEXT INDEX ft_student (Sname, Email, Phone);
DROP INDEX IF EXISTS ft_course ON Course;
ALTER TABLE Course
  ADD FULLTEXT INDEX ft_course (Cname);
DROP INDEX IF EXISTS ft_teacher ON Teacher;
ALTER TABLE Teacher
  ADD FULLTEXT INDEX ft_teacher (Tname, Email);

/*
 * 8. 视图
 */
CREATE OR REPLACE VIEW v_search_entities AS
SELECT 'student' AS etype, s.Sno AS id, s.Sname AS name, s.Email AS ext, d.Dname AS dept
FROM Student s LEFT JOIN Department d ON s.Dno = d.Dno
UNION ALL
SELECT 'course', c.Cno, c.Cname, d.Dname, d.Dname
FROM Course c LEFT JOIN Department d ON c.Dno = d.Dno
UNION ALL
SELECT 'teacher', t.Tno, t.Tname, t.Email, d.Dname
FROM Teacher t LEFT JOIN Department d ON t.Dno = d.Dno;

CREATE OR REPLACE VIEW v_sc_detailed AS
SELECT
  s.Sno,
  s.Sname,
  s.Dno AS StudentDept,
  c.Cno,
  c.Cname,
  c.Credits,
  sc.YearTaken,
  sc.Term,
  sc.Grade,
  sc.Status,
  gs.Letter,
  gs.Point AS GradePoint
FROM SC sc
JOIN Student s ON sc.Sno = s.Sno
JOIN Course c ON sc.Cno = c.Cno
LEFT JOIN GradeScale gs
  ON sc.Grade IS NOT NULL
 AND sc.Grade BETWEEN gs.MinScore AND gs.MaxScore;

CREATE OR REPLACE VIEW v_student_term_gpa AS
SELECT
  Sno,
  YearTaken,
  Term,
  SUM(GradePoint * Credits) / NULLIF(SUM(Credits),0) AS TermGPA,
  COUNT(*) AS CourseCount
FROM v_sc_detailed
WHERE Status = 'completed' AND Grade IS NOT NULL
GROUP BY Sno, YearTaken, Term;

CREATE OR REPLACE VIEW v_student_cum_gpa AS
SELECT
  t.Sno,
  t.YearTaken,
  t.Term,
  SUM(t.TermGPA * t.CourseCount) OVER (PARTITION BY Sno ORDER BY YearTaken, Term
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
  /
  NULLIF(SUM(t.CourseCount) OVER (PARTITION BY Sno ORDER BY YearTaken, Term
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),0) AS CumulativeGPA
FROM v_student_term_gpa t;

CREATE OR REPLACE VIEW v_course_stats AS
SELECT
  c.Cno,
  c.Cname,
  COUNT(*) AS TakenCount,
  AVG(sc.Grade) AS AvgScore,
  STDDEV_SAMP(sc.Grade) AS StdDevScore,
  SUM(CASE WHEN sc.Grade >= 60 THEN 1 ELSE 0 END) / COUNT(*) AS PassRate
FROM SC sc
JOIN Course c ON sc.Cno = c.Cno
WHERE sc.Status = 'completed' AND sc.Grade IS NOT NULL
GROUP BY c.Cno, c.Cname;

/*
 * 9. 触发器
 */
DROP TRIGGER IF EXISTS trg_sc_before_insert;
DROP TRIGGER IF EXISTS trg_sc_before_update;
DROP TRIGGER IF EXISTS trg_course_prereq_cycle_insert;
DROP TRIGGER IF EXISTS trg_course_prereq_cycle_update;

DELIMITER $$

-- 检查选课时是否满足先修课要求
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
    WHERE Sno = NEW.Sno
      AND Cno = v_prereq
      AND Grade IS NOT NULL
      AND Grade >= 60
      AND Status = 'completed';

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
  DECLARE v_prereq VARCHAR(10);
  DECLARE v_ok INT DEFAULT 0;

  IF NEW.Cno <> OLD.Cno THEN
    SELECT PrereqCno INTO v_prereq
    FROM Course WHERE Cno = NEW.Cno;

    IF v_prereq IS NOT NULL THEN
      SELECT COUNT(*) INTO v_ok
      FROM SC
      WHERE Sno = NEW.Sno
        AND Cno = v_prereq
        AND Grade IS NOT NULL
        AND Grade >= 60
        AND Status = 'completed';

      IF v_ok = 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Prerequisite not satisfied on update.';
      END IF;
    END IF;
  END IF;
END$$

-- 防止课程先修课形成环（INSERT + UPDATE）
CREATE TRIGGER trg_course_prereq_cycle_insert
BEFORE INSERT ON Course
FOR EACH ROW
BEGIN
  DECLARE v_cycle INT DEFAULT 0;

  IF NEW.PrereqCno IS NOT NULL THEN
    WITH RECURSIVE chain AS (
      SELECT Cno, PrereqCno FROM Course WHERE Cno = NEW.PrereqCno
      UNION ALL
      SELECT c.Cno, c.PrereqCno
      FROM Course c
      JOIN chain ch ON c.Cno = ch.PrereqCno
      WHERE c.PrereqCno IS NOT NULL
    )
    SELECT 1 INTO v_cycle FROM chain WHERE PrereqCno = NEW.Cno LIMIT 1;

    IF v_cycle = 1 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Prerequisite cycle detected on insert';
    END IF;
  END IF;
END$$

CREATE TRIGGER trg_course_prereq_cycle_update
BEFORE UPDATE ON Course
FOR EACH ROW
BEGIN
  DECLARE v_cycle INT DEFAULT 0;

  IF NEW.PrereqCno IS NOT NULL AND NEW.PrereqCno <> OLD.PrereqCno THEN
    WITH RECURSIVE chain AS (
      SELECT Cno, PrereqCno FROM Course WHERE Cno = NEW.PrereqCno
      UNION ALL
      SELECT c.Cno, c.PrereqCno
      FROM Course c
      JOIN chain ch ON c.Cno = ch.PrereqCno
      WHERE c.PrereqCno IS NOT NULL
    )
    SELECT 1 INTO v_cycle FROM chain WHERE PrereqCno = NEW.Cno LIMIT 1;

    IF v_cycle = 1 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Prerequisite cycle detected on update';
    END IF;
  END IF;
END$$

DELIMITER ;

/*
 * 完成
 */
