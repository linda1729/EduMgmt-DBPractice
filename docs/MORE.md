# A. 面向“多关键字检索”的结构与索引

## A1) FULLTEXT 全文索引（英文/拼音检索友好）

> 适合课程名、学生名、教师名等“文本字段”多关键词检索。
>  说明：MySQL InnoDB 的 `FULLTEXT` 对英文/拼音效果好；中文精确分词建议使用 `ngram` parser（需要安装）或切到 ES/Meilisearch。如果先用 MySQL，中文可退而求其次用 LIKE/拼音列。

```sql
-- 学生、课程、教师建立 FULLTEXT 索引
ALTER TABLE Student ADD FULLTEXT ft_student (Sname, Email, Phone);
ALTER TABLE Course  ADD FULLTEXT ft_course  (Cname);
ALTER TABLE Teacher ADD FULLTEXT ft_teacher (Tname, Email);
```

使用示例（布尔模式多关键词）：

```sql
-- 例：搜索“data AND algorithm NOT writing”
SELECT Cno, Cname FROM Course
WHERE MATCH(Cname) AGAINST('+data +algorithm -writing' IN BOOLEAN MODE);
```

## A2) 统一“可检索文本”视图（跨表联查）

> 为前端一次输入多关键词 -> 一次查“人/课/教师/院系”的入口。

```sql
CREATE OR REPLACE VIEW v_search_entities AS
SELECT 'student' AS etype, s.Sno AS id, s.Sname AS name, s.Email AS ext, d.Dname AS dept
FROM Student s LEFT JOIN Department d ON s.Dno = d.Dno
UNION ALL
SELECT 'course', c.Cno, c.Cname, d.Dname, d.Dname
FROM Course c LEFT JOIN Department d ON c.Dno = d.Dno
UNION ALL
SELECT 'teacher', t.Tno, t.Tname, t.Email, d.Dname
FROM Teacher t LEFT JOIN Department d ON t.Dno = d.Dno;
```

> 简单 LIKE 多关键词（兼容中文）：

```sql
-- 关键词数组由后端拆成多段 AND 组合
-- 示例：kw1='数据', kw2='结构'
SELECT * FROM v_search_entities
WHERE (name LIKE CONCAT('%','数据','%') OR ext LIKE CONCAT('%','数据','%') OR dept LIKE CONCAT('%','数据','%'))
  AND (name LIKE CONCAT('%','结构','%') OR ext LIKE CONCAT('%','结构','%') OR dept LIKE CONCAT('%','结构','%'));
```

> 如果你可以安装 ngram parser（MySQL 8 for InnoDB），可为中文加：

```sql
-- 示例（需要已安装 ngram parser）
-- ALTER TABLE Course ADD FULLTEXT ft_course_ngram (Cname) WITH PARSER ngram;
```

## A3) 组合索引优化“复杂筛选”

> 典型筛选：院系 + 学年学期 + 课程/教师 + 成绩区间

```sql
CREATE INDEX idx_sc_student_term ON SC (Sno, YearTaken, Term);
CREATE INDEX idx_sc_course_term  ON SC (Cno, YearTaken, Term);
CREATE INDEX idx_sc_grade        ON SC (Grade);
CREATE INDEX idx_course_dept_active ON Course (Dno, IsActive);
CREATE INDEX idx_teaching_dept_time ON Teaching (YearOffered, Term, Cno, Tno);
```

------

# B. 成绩统计分析：视图/物化聚合/成绩点换算

## B1) 成绩等级与绩点映射表（灵活配置）

```sql
CREATE TABLE IF NOT EXISTS GradeScale (
  MinScore DECIMAL(5,2) NOT NULL,
  MaxScore DECIMAL(5,2) NOT NULL,
  Letter   VARCHAR(2)   NOT NULL,
  Point    DECIMAL(3,2) NOT NULL,
  CHECK (MinScore <= MaxScore)
);

-- 示例：可按学校实际改
TRUNCATE GradeScale;
INSERT INTO GradeScale VALUES
(93,100,'A',4.0),(90,92.99,'A-',3.7),
(87,89.99,'B+',3.3),(83,86.99,'B',3.0),(80,82.99,'B-',2.7),
(77,79.99,'C+',2.3),(73,76.99,'C',2.0),(70,72.99,'C-',1.7),
(60,69.99,'D',1.0),(0,59.99,'F',0.0);
```

## B2) 课程-学生明细视图（附绩点/等级）

```sql
CREATE OR REPLACE VIEW v_sc_detailed AS
SELECT
  s.Sno, s.Sname, s.Dno AS StudentDept,
  c.Cno, c.Cname, c.Credits,
  sc.YearTaken, sc.Term, sc.Grade, sc.Status,
  gs.Letter,
  gs.Point AS GradePoint
FROM SC sc
JOIN Student s ON sc.Sno = s.Sno
JOIN Course  c ON sc.Cno = c.Cno
LEFT JOIN GradeScale gs
  ON sc.Grade IS NOT NULL
 AND sc.Grade BETWEEN gs.MinScore AND gs.MaxScore;
```

## B3) 学生学期/累计 GPA 视图（窗口函数）

```sql
-- 学期 GPA（仅统计 completed 且有成绩的记录）
CREATE OR REPLACE VIEW v_student_term_gpa AS
SELECT
  Sno, YearTaken, Term,
  SUM(GradePoint * Credits) / NULLIF(SUM(Credits),0) AS TermGPA,
  COUNT(*) AS CourseCount
FROM v_sc_detailed
WHERE Status='completed' AND Grade IS NOT NULL
GROUP BY Sno, YearTaken, Term;

-- 累计 GPA（到每个学期为止，使用窗口函数做累积）
CREATE OR REPLACE VIEW v_student_cum_gpa AS
SELECT
  t.Sno,
  t.YearTaken, t.Term,
  SUM(t.TermGPA * t.CourseCount) OVER (PARTITION BY Sno ORDER BY YearTaken, Term
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
  /
  SUM(t.CourseCount) OVER (PARTITION BY Sno ORDER BY YearTaken, Term
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
  AS CumulativeGPA
FROM v_student_term_gpa t;
```

## B4) 课程统计视图（均分、标准差、通过率、分布）

```sql
CREATE OR REPLACE VIEW v_course_stats AS
SELECT
  c.Cno, c.Cname,
  COUNT(*)                              AS TakenCount,
  AVG(sc.Grade)                         AS AvgScore,
  STDDEV_SAMP(sc.Grade)                 AS StdDevScore,
  SUM(CASE WHEN sc.Grade >= 60 THEN 1 ELSE 0 END) / COUNT(*) AS PassRate
FROM SC sc
JOIN Course c ON sc.Cno = c.Cno
WHERE sc.Status='completed' AND sc.Grade IS NOT NULL
GROUP BY c.Cno, c.Cname;
```

> 如果需要“分位数/区间分布”，可以建**物化统计表**（用事件或后端任务刷新），例如：

```sql
CREATE TABLE IF NOT EXISTS CourseAggDaily (
  StatDate    DATE NOT NULL,
  Cno         VARCHAR(10) NOT NULL,
  TakenCount  INT NOT NULL,
  AvgScore    DECIMAL(6,2) NULL,
  StdDevScore DECIMAL(6,2) NULL,
  PassRate    DECIMAL(6,4) NULL,
  PRIMARY KEY (StatDate, Cno),
  FOREIGN KEY (Cno) REFERENCES Course(Cno) ON DELETE CASCADE
);
```

------

# C. 复杂业务/数据完整性增强

## C1) 防止“先修课环”造成循环依赖

> `PrereqCno` 是单列，但仍可能出现 A→B→A。用 **递归 CTE** 在写入时自检（用触发器实现）。

```sql
DELIMITER $$

CREATE TRIGGER trg_course_prereq_cycle
BEFORE UPDATE ON Course
FOR EACH ROW
BEGIN
  IF NEW.PrereqCno IS NOT NULL AND NEW.PrereqCno <> OLD.PrereqCno THEN
    WITH RECURSIVE chain AS (
      SELECT Cno, PrereqCno FROM Course WHERE Cno = NEW.PrereqCno
      UNION ALL
      SELECT c.Cno, c.PrereqCno FROM Course c
      JOIN chain ch ON c.Cno = ch.PrereqCno
      WHERE c.PrereqCno IS NOT NULL
    )
    SELECT 1 INTO @hasCycle FROM chain WHERE PrereqCno = NEW.Cno LIMIT 1;

    IF @hasCycle = 1 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Prerequisite cycle detected';
    END IF;
    SET @hasCycle = NULL;
  END IF;
END$$

DELIMITER ;
```

> 如需在 INSERT 时同样校验，可复制为 `BEFORE INSERT` 版本。

## C2) 审计/时间戳（便于追溯与界面“最近更新”排序）

```sql
ALTER TABLE Student  ADD COLUMN CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                     ADD COLUMN UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE Course   ADD COLUMN CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                     ADD COLUMN UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE Teacher  ADD COLUMN CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                     ADD COLUMN UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE SC       ADD COLUMN UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
```

------

# D. 供“复杂查询/前端界面”直接使用的 SQL 模板

## D1) 学生多条件组合检索（姓名关键词 + 院系 + 入学年 + 课程关键词 + 老师关键词 + 成绩区间）

```sql
-- :kwName, :dept, :yearFrom, :yearTo, :kwCourse, :kwTeacher, :minGrade, :maxGrade 由后端按需传入
SELECT DISTINCT s.Sno, s.Sname, d.Dname AS Dept, s.EnrollYear
FROM Student s
LEFT JOIN Department d ON s.Dno = d.Dno
LEFT JOIN SC sc ON sc.Sno = s.Sno
LEFT JOIN Course c ON c.Cno = sc.Cno
LEFT JOIN Teaching tg ON tg.Cno = c.Cno AND tg.YearOffered = sc.YearTaken AND tg.Term = sc.Term
LEFT JOIN Teacher t ON t.Tno = tg.Tno
WHERE (:kwName IS NULL OR s.Sname LIKE CONCAT('%', :kwName, '%'))
  AND (:dept   IS NULL OR s.Dno = :dept)
  AND (:yearFrom IS NULL OR s.EnrollYear >= :yearFrom)
  AND (:yearTo   IS NULL OR s.EnrollYear <= :yearTo)
  AND (:kwCourse IS NULL OR c.Cname LIKE CONCAT('%', :kwCourse, '%'))
  AND (:kwTeacher IS NULL OR t.Tname LIKE CONCAT('%', :kwTeacher, '%'))
  AND (:minGrade IS NULL OR sc.Grade >= :minGrade)
  AND (:maxGrade IS NULL OR sc.Grade <= :maxGrade);
```

## D2) 某学生的成绩分析卡片（学期 GPA、累计 GPA、通过率、分布）

```sql
-- 学期 GPA 与累计 GPA
SELECT g.Sno, g.YearTaken, g.Term, g.TermGPA, cg.CumulativeGPA
FROM v_student_term_gpa g
JOIN v_student_cum_gpa  cg
  ON g.Sno = cg.Sno AND g.YearTaken = cg.YearTaken AND g.Term = cg.Term
WHERE g.Sno = :sno
ORDER BY g.YearTaken, g.Term;

-- 该生成绩通过率与区间分布（示例：60、70、80、90 档）
SELECT
  SUM(Grade >= 60) / COUNT(*) AS PassRate,
  SUM(Grade < 60)  AS cntF,
  SUM(Grade BETWEEN 60 AND 69.99) AS cntD,
  SUM(Grade BETWEEN 70 AND 79.99) AS cntC,
  SUM(Grade BETWEEN 80 AND 89.99) AS cntB,
  SUM(Grade >= 90) AS cntA
FROM SC
WHERE Sno = :sno AND Status='completed' AND Grade IS NOT NULL;
```

## D3) 课程难度画像（均分、Std、通过率、先修影响）

```sql
-- 单课程年度学期维度统计
SELECT sc.YearTaken, sc.Term,
       COUNT(*) AS Taken, AVG(sc.Grade) AS AvgScore,
       STDDEV_SAMP(sc.Grade) AS StdDev, 
       SUM(sc.Grade >= 60)/COUNT(*) AS PassRate
FROM SC sc
WHERE sc.Cno = :cno AND sc.Status='completed' AND sc.Grade IS NOT NULL
GROUP BY sc.YearTaken, sc.Term
ORDER BY sc.YearTaken, sc.Term;

-- 先修课 vs 本课成绩（简易相关性观察）
SELECT p.Cno AS PrereqCno, p.Cname AS PrereqName,
       AVG(scP.Grade) AS AvgPrereq, AVG(sc.Grade) AS AvgThis
FROM Course c
JOIN Course p ON c.PrereqCno = p.Cno
JOIN SC sc  ON sc.Cno  = c.Cno  AND sc.Status='completed' AND sc.Grade IS NOT NULL
JOIN SC scP ON scP.Cno = p.Cno AND scP.Sno = sc.Sno AND scP.Status='completed' AND scP.Grade IS NOT NULL
WHERE c.Cno = :cno
GROUP BY p.Cno, p.Cname;
```

------

# E. 体验与工程化小优化

1. **分页与排序**：所有列表加 `ORDER BY` + `LIMIT/OFFSET`；常用排序如 `UpdatedAt DESC`、`AvgScore DESC`。
2. **软删除**：对 `Student/Course/Teacher` 可加 `IsActive` 字段，避免误删带来的外键连锁。
3. **幂等导入**：所有初始化脚本使用 `IF NOT EXISTS` / `INSERT ... ON DUPLICATE KEY UPDATE`。
4. **API 一致性**：前端复杂检索统一走“查询服务”，把多条件拼装转成上面的模板 SQL，避免在前端直接拼 SQL。
5. **报表导出**：统计视图（如 `v_course_stats`、`v_student_term_gpa`）直接用于 Excel/CSV 导出。



