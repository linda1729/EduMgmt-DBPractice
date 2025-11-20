# 文件夹作用说明

| 路径 | 主要职责 |
| --- | --- |
| `app/` | Flask 应用主包，包含配置、模型、视图、API、服务等业务代码。 |
| `app/api/` | 面向外部的 REST API 蓝图，实现学生、课程、选课等 JSON 接口。 |
| `app/repositories/` | 数据访问层，封装学生/课程/选课的查询与持久化逻辑。 |
| `app/services/` | 运行时服务与批处理脚本（如演示数据填充、报表生成）。 |
| `app/templates/` | Jinja2 模板，用于渲染管理端 HTML 页面。 |
| `app/static/` | 静态资源（CSS、JavaScript、图片等），供模板和前端使用。 |
| `docs/` | 项目文档与设计说明（设计思路、需求分析、变更记录等）。 |
| `migrations/` | Alembic/Flask-Migrate 迁移脚本与环境（包含历史版本目录）。 |
| `SQL/` | 初始化与演示用的独立 SQL 脚本（schema 与示例数据）。 |
| `media/` | 媒体素材，例如产品 logo、示意图等资源。 |

> 说明：根目录下的 `requirements.txt` 指定运行依赖，`AGENTS.md`、`DESIGN.md` 等文档提供补充背景，可与本表结合阅读以快速定位需要的模块。
