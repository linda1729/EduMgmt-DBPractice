# 仓库目录结构

> 生成时间：$(date -u +"%Y-%m-%d %H:%M:%S UTC")，对 `.venv*`、`.idea/` 等体量巨大的开发环境仅列出顶层节点，便于阅读。

## 顶层概览

- `.env`：本地开发环境变量示例。
- `.venv/`、`.venv_codex/`：不同来源的 Python 虚拟环境，未展开。
- `AGENTS.md`、`DESIGN.md`、`docs/`：项目规范、设计与补充文档。
- `SQL/`：`schema.sql` 与多份初始化数据脚本。
- `app/`：Flask 应用源码（配置、模型、模板、静态资源等）。
- `migrations/`：Alembic 迁移脚本及环境设置。
- `media/`：演示使用的图片资源。
- `requirements.txt`：运行依赖清单。
- `instance/dev.db`：本机 SQLite 演示数据库（自动生成，可删除重建）。

## 结构树（业务相关目录展开）

```text
flask-edu-mgmt/
├── .env
├── .venv/
├── .venv_codex/
├── AGENTS.md
├── SQL/
│   ├── classroom_data.sql
│   ├── course_data.sql
│   ├── SC_data.sql
│   ├── schema.sql
│   ├── student_data.sql
│   ├── teacher_data.sql
│   └── teaching_data.sql
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── courses.py
│   │   ├── enrollments.py
│   │   └── students.py
│   ├── cli.py
│   ├── config.py
│   ├── db_init.py
│   ├── extensions.py
│   ├── models.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── course_repository.py
│   │   ├── enrollment_repository.py
│   │   └── student_repository.py
│   ├── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── seed_service.py
│   ├── static/
│   │   └── css/
│   │       └── main.css
│   │       └── js/
│   │       ├── chart.umd.min.js
│   └── templates/
│       ├── base.html
│       ├── classrooms.html
│       ├── courses.html
│       ├── enrollments.html
│       ├── index.html
│       ├── students.html
│       ├── teachers.html
│       └── teachings.html
├── docs/
│   ├── ConversationChanges.md
│   ├── DESIGN.md
│   ├── folder_overview.md
│   ├── MORE.md
│   └── requirement_analysis.md
├── media/
│   └── linda1729icon.png
├── migrations/
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_baseline.py
├── requirements.txt
└── SQL/ (见上)
```

> 若需包含被折叠的虚拟环境或 IDE 配置详情，可运行 `python scripts`/`find` 命令重新导出完整树，但通常无需纳入代码评审。
