# Conversation Changes

- 批量造数：新增 `app/services/seed_service.py` 并在 `app/cli.py` 注册 `seed-demo` 命令，为各表生成约 100 条样例数据，同时在 `AGENTS.md` 补充使用说明。
- 需求分析：新增并调整 `docs/requirement_analysis.md`，聚焦数据库实验场景，弱化性能/安全等企业级要求，同时保留复杂查询和统计需求。
- 最小前端：在 `app/routes.py` 改为渲染模板并新增 `/health` 接口，新增 `app/templates/base.html` 与 `app/templates/index.html`，提供可启动预览的最小界面。
- 数据驱动：手动初始化 `migrations/` 目录准备迁移基线，扩展 `app/routes.py` 以汇总数据库数据并提供学生增删改查能力，新建 `app/templates/students.html` 并更新首页模板展示实时统计。
- 管理后台：大幅扩展 `app/routes.py` 实现学生、课程、选课、教师、教室及授课安排的增删查改逻辑；新增对应模板（`courses.html`、`enrollments.html`、`teachers.html`、`classrooms.html`、`teachings.html`）并完善导航，以支撑基于 MySQL 数据的完整教务管理流程。
- 前端美化：引入全局样式表 `app/static/css/main.css`、更新 `base.html` 字体与导航，并重塑主要页面卡片/表格视觉，统一色彩与交互反馈，提升整体界面体验。
- 渐变主题：调整 `app/static/css/main.css` 至浅蓝紫渐变基调，统一所有页面为居中排版与渐变卡片效果，对各管理模板及首页入口卡片/统计表格布局进行更新以匹配新视觉规范。
- 数据可视化与模糊检索：为学生、课程、选课、教师、教室、授课六大模块模板新增梯度统计卡片、Chart.js 可视化图表及前端模糊搜索功能，并在 `app/routes.py` 汇总相应统计数据。
- 中文批注与目录导览：在 `app/` 和 `migrations/` 中所有有意义的函数前新增“功能”中文批注，便于快速理解逻辑；同时新增 `docs/folder_overview.md` 记录仓库各文件夹作用供查阅。
- 首页导航可用性：将仪表盘 Feature 卡片改为支持 `stretched-link` 的容器并确保学生/课程等入口可点击跳转，顺便移除“下一步开发建议”板块及对应样式，聚焦核心操作。
- 导航去重与装饰优化：删除仪表盘上的功能跳转卡片，保留顶部导航即可触达全部模块；各管理页的“新增”表单去掉多余图形装饰，页面更简洁。
- 统一 Bootstrap 风格：调整 `base.html` 导航为官方 `navbar`，重构首页与各管理页卡片/统计布局以使用 Bootstrap 卡片与表格组件，精简自定义 CSS（`app/static/css/main.css`）并移除冗余装饰，让界面更疏朗。
- 首页可视化增强：在 `index.html` 新增热门课程柱状图与选课状态环形图，路由返回相应统计数据供 Chart.js 渲染，满足可视化需求。
- 路径与自增修复：在 `app/config.py` 正确指向 `SQL/schema.sql` 并允许自定义路径，同时将 `Teaching.TeachID` 映射为跨数据库自增（`app/models.py`），确保 CLI 初始化和演示数据填充、统计图渲染流程可用。
- 目录索引：新增 `docs/directory_structure.md` 输出当前仓库完整树形结构，帮助快速定位需要修改的模块或静态资源。
