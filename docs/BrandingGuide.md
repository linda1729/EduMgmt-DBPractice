# 品牌与图片更换指南

本项目的 UI 由 React + CoreUI 驱动，品牌素材集中在 `frontend/` 目录。下面列出常见的 Logo、图标与头像入口，以及推荐的替换方式。

## 1. 导航栏 Logo（Sidebar / Header）

| 位置 | 文件 | 说明 |
| --- | --- | --- |
| 侧边栏展开状态 Logo | `frontend/src/assets/brand/logo.js` | 导出一个包含 SVG 字符串的数组，供 `AppSidebar` 引用。 |
| 侧边栏折叠状态 Sygnet | `frontend/src/assets/brand/sygnet.js` | 用于窄屏模式的迷你图标。 |
| 引用位置 | `frontend/src/components/AppSidebar.js` | `logo` 与 `sygnet` 分别渲染在 `CSidebarBrand` 中。 |

**替换方法：**
1. 准备新的 SVG 向量文件，建议宽高与当前字符串一致（`logo` 默认 viewBox 为 `599 116`，`sygnet` 为 `118 46`），以免出现拉伸。
2. 用文本编辑器打开 `logo.js` / `sygnet.js`，将模板字符串中的 `<svg>` 内容替换为你的 SVG（仅保留 `<g>...</g>` 片段也可，CoreUI 会包裹在 `<svg>` 中）。
3. 保存后运行 `npm start` 即可看到更新。若使用 PNG，请先在线转换为 SVG，再替换到文件中。

## 2. 浏览器 Favicon / PWA 图标

| 资源 | 文件 | 说明 |
| --- | --- | --- |
| 主 favicon | `frontend/public/favicon.ico` | 被 `frontend/index.html` 的 `<link rel="shortcut icon" ...>` 引用（参见文件行 18-20）。 |
| PWA manifest 图标 | `frontend/public/manifest.json` | 默认指向 `./assets/img/favicon.png`，可改为自定义 PNG（需要在 `frontend/public/assets/img/` 下提供对应文件）。 |

**替换方法：**
1. 将新的 `favicon.ico` 放入 `frontend/public/`，保持同名即可。
2. 如需适配桌面快捷方式或移动端安装提示，可在 `manifest.json` 的 `icons` 数组中添加多种尺寸 PNG，并将文件放入 `frontend/public/assets/img/`。

## 3. 头像与示例图片

| 位置 | 文件 | 说明 |
| --- | --- | --- |
| 右上角头像 | `frontend/src/components/header/AppHeaderDropdown.js` | 目前引用 `frontend/src/assets/images/avatars/8.jpg`。 |
| 头像素材库 | `frontend/src/assets/images/avatars/` | 可以放置自定义 JPG/PNG。 |
| 其他示例图 | `frontend/src/assets/images/` | 包含若干演示用背景图，可按需替换或删除。 |

**替换方法：**
1. 将新的头像图（建议 128×128 以上、JPG/PNG 均可）放入 `frontend/src/assets/images/avatars/`。
2. 编辑 `AppHeaderDropdown.js`，将 `import avatar8 ...` 改为你的文件路径，例如 `import avatarAdmin from 'src/assets/images/avatars/admin.png'`。
3. 如果需要在仪表盘、卡片等位置展示品牌图片，可在相应的视图文件中新增 `import` 并使用 `<img />` 渲染。

## 4. 登录页 / 其他页面背景

当前项目未单独实现登录页背景，若后续需要，可在对应视图（如 `frontend/src/views/pages/login/Login.js`，若已创建）中引入图片资源，并在 `src/scss` 中调整样式。建议统一将自定义图片放在 `frontend/src/assets/images/` 下，便于打包。

## 5. 后端（Flask）模板遗留

如果你仍在使用 `app/templates/` 下的 Jinja 页面，可以在 `app/static` 内维护传统的 CSS/图片资源：

| 资源 | 说明 |
| --- | --- |
| `app/static/css/main.css` | 模板的全局样式。 |
| `app/static/` 下的自定义图片 | 可放置旧版 Logo、背景等，并在模板中通过 `url_for('static', filename='images/xxx.png')` 引用。 |

与 React 前端无交集时，可忽略该部分。

---

> **建议**：替换素材后，执行 `npm run build` 验证打包结果是否正常；若在生产环境部署，也请清除浏览器缓存以看到最新的 favicon 与 SVG。
