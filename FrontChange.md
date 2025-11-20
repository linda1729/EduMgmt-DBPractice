一份**“用 CoreUI Free React Admin 替换现有前端”的完整落地方案**。按这个做，你的 Flask 继续当后端 API，前端全部交给 CoreUI 的 React 模板。

------

# 方案总览（前后端分离）

- **后端（Flask）**：只提供 JSON API（/api/...），不再渲染 Jinja2 模板。
- **前端（React + CoreUI）**：单独项目放在 `frontend/`，通过 `fetch/axios` 调用 Flask 的 API。
- **运行**：本地两个进程启动；部署时可分开部署，或让 Flask 直接托管 React 的打包文件。

------

## 第 0 步：目录与“要改/要加/要删”的清单

### 需要“停用/备份”的内容

- `app/templates/`（整包备份或删除，不再使用 Jinja）
- `app/static/css/main.css` 及旧 JS（不再承担页面样式/交互；保留也行）

### 需要“修改/新增”的内容

- `app/__init__.py`：启用 CORS
- `app/routes.py`：只保留/新增 API 路由注册（不再 `render_template`）
- `app/api/*`：补齐 REST JSON 接口（分页/排序/筛选）
- （可选）新增 `app/api/auth.py`：登录换 token（若需要鉴权）
- 新增 `frontend/`：放 CoreUI React 前端
- （可选）新增 `app/serve_frontend.py`：让 Flask 托管打包后的 React

------

## 第 1 步：后端（Flask）改造

### 1.1 安装 CORS

```bash
pip install flask-cors
```

**app/\**init\**.py**

```python
from flask import Flask
from flask_cors import CORS
from .extensions import db  # 你已有的
# from .api import students, courses, enrollments  # 下面会注册

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    db.init_app(app)

    # 允许前端跨域访问
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册 API 蓝图
    from .api.students import bp as students_bp
    from .api.courses import bp as courses_bp
    from .api.enrollments import bp as enrollments_bp
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(courses_bp, url_prefix="/api/courses")
    app.register_blueprint(enrollments_bp, url_prefix="/api/enrollments")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
```

### 1.2 API 风格建议（统一返回）

- 成功：`{"data": ..., "meta": {...}}`
- 失败：`{"error": {"code": "...","message": "..."}}, 4xx/5xx`

**分页/筛选/排序**通用 query 参数：`?page=1&page_size=20&search=xxx&sort=created_at,-name`

**app/api/students.py（示例）**

```python
from flask import Blueprint, request
from app.models import Student, db

bp = Blueprint("students", __name__)

@bp.get("")
def list_students():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    search = request.args.get("search", "")
    q = Student.query
    if search:
        q = q.filter(Student.name.ilike(f"%{search}%"))
    total = q.count()
    items = q.order_by(Student.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {
        "data": [s.to_dict() for s in items],
        "meta": {"page": page, "page_size": page_size, "total": total}
    }

@bp.post("")
def create_student():
    payload = request.get_json() or {}
    s = Student(**payload)
    db.session.add(s)
    db.session.commit()
    return {"data": s.to_dict()}, 201

@bp.get("/<int:student_id>")
def get_student(student_id):
    s = Student.query.get_or_404(student_id)
    return {"data": s.to_dict()}

@bp.put("/<int:student_id>")
def update_student(student_id):
    s = Student.query.get_or_404(student_id)
    payload = request.get_json() or {}
    for k,v in payload.items():
        setattr(s, k, v)
    db.session.commit()
    return {"data": s.to_dict()}

@bp.delete("/<int:student_id>")
def delete_student(student_id):
    s = Student.query.get_or_404(student_id)
    db.session.delete(s)
    db.session.commit()
    return {"data": True}
```

> 按同样套路完善 `courses.py / enrollments.py`。
>  可选：新增 `/api/dashboard/metrics` 返回首页卡片与图表数据（总学生数、课程数、近 7 日新增等）。

------

## 第 2 步：前端（CoreUI React）落地

### 2.1 拉取到 `frontend/`

```bash
cd flask-edu-mgmt
npx create-react-app frontend --template coreui  # 若官方提供模板脚手架
# 或者：git clone CoreUI 的 react 模板仓库到 frontend/
cd frontend
npm install
```

> 如果模板是 Vite 版，按其 README 初始化；不影响后续步骤。

### 2.2 配置 API 地址

**方案 A：env 变量**

- `.env`（React）：

  ```
  REACT_APP_API_BASE_URL=http://127.0.0.1:5000
  ```

**src/api/client.ts / client.js**

```js
export const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000"

export async function apiGet(path, params={}){
  const url = new URL(API_BASE + path)
  Object.entries(params).forEach(([k,v]) => url.searchParams.set(k, v))
  const res = await fetch(url, { credentials: "omit" })
  if(!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function apiJSON(path, method, body) {
  const res = await fetch(API_BASE + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if(!res.ok) throw new Error(await res.text())
  return res.json()
}
```

**方案 B：开发代理（省去写全域名）**

- `package.json` 增加：

  ```json
  "proxy": "http://127.0.0.1:5000"
  ```

  这样前端里可以直接请求 `/api/...`。

### 2.3 路由与页面（React Router + CoreUI 组件）

在 CoreUI 模板的 `src/routes.tsx`（或同名）里加入你的模块路由：

```tsx
// Students / Courses / Enrollments 页面
const Students = React.lazy(() => import('./views/students/Students'))
const StudentForm = React.lazy(() => import('./views/students/StudentForm'))
const Courses = React.lazy(() => import('./views/courses/Courses'))
const Enrollments = React.lazy(() => import('./views/enrollments/Enrollments'))

const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard },
  { path: '/students', name: 'Students', component: Students },
  { path: '/students/new', name: 'New Student', component: StudentForm },
  { path: '/students/:id/edit', name: 'Edit Student', component: StudentForm },
  { path: '/courses', name: 'Courses', component: Courses },
  { path: '/enrollments', name: 'Enrollments', component: Enrollments },
]
export default routes
```

左侧导航（`src/_nav.ts`）改为你的教务菜单：

```ts
const _nav = [
  { component: CNavItem, name: 'Dashboard', to: '/dashboard', icon: <CIcon icon={cilSpeedometer}/> },
  { component: CNavTitle, name: 'Academics' },
  { component: CNavItem, name: 'Students', to: '/students', icon: <CIcon icon={cilUser}/> },
  { component: CNavItem, name: 'Teachers', to: '/teachers', icon: <CIcon icon={cilPeople}/> },
  { component: CNavItem, name: 'Courses', to: '/courses', icon: <CIcon icon={cilLibrary}/> },
  { component: CNavItem, name: 'Enrollments', to: '/enrollments', icon: <CIcon icon={cilTask}/> },
]
export default _nav
```

### 2.4 示例页面（Students 列表 + 新建/编辑）

**src/views/students/Students.tsx**

```tsx
import React, { useEffect, useState } from 'react'
import { CCard, CCardBody, CCardHeader, CButton, CTable, CTableHead, CTableRow, CTableHeaderCell, CTableBody, CTableDataCell, CInputGroup, CFormInput } from '@coreui/react'
import { apiGet, apiJSON } from '../../api/client'
import { useHistory } from 'react-router-dom'

export default function Students() {
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const history = useHistory()

  async function load(page=1){
    const res = await apiGet('/api/students', { page, page_size: 20, search })
    setRows(res.data); setTotal(res.meta.total)
  }
  useEffect(() => { load() }, []) // 首次加载

  async function onDelete(id:number){
    if(!window.confirm('确认删除该学生？')) return
    await apiJSON(`/api/students/${id}`, 'DELETE', null)
    load()
  }

  return (
    <CCard>
      <CCardHeader className="d-flex justify-content-between align-items-center">
        <div>Students ({total})</div>
        <div className="d-flex gap-2">
          <CInputGroup>
            <CFormInput placeholder="Search name..." value={search} onChange={(e)=>setSearch(e.target.value)} />
            <CButton onClick={()=>load()}>Search</CButton>
          </CInputGroup>
          <CButton color="primary" onClick={()=>history.push('/students/new')}>+ New</CButton>
        </div>
      </CCardHeader>
      <CCardBody>
        <CTable hover responsive>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell>#</CTableHeaderCell>
              <CTableHeaderCell>Name</CTableHeaderCell>
              <CTableHeaderCell>Gender</CTableHeaderCell>
              <CTableHeaderCell>Class</CTableHeaderCell>
              <CTableHeaderCell>Actions</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            {rows.map((r:any)=>(
              <CTableRow key={r.id}>
                <CTableDataCell>{r.id}</CTableDataCell>
                <CTableDataCell>{r.name}</CTableDataCell>
                <CTableDataCell>{r.gender}</CTableDataCell>
                <CTableDataCell>{r.class_name}</CTableDataCell>
                <CTableDataCell className="d-flex gap-2">
                  <CButton size="sm" color="info" variant="outline" onClick={()=>history.push(`/students/${r.id}/edit`)}>Edit</CButton>
                  <CButton size="sm" color="danger" variant="outline" onClick={()=>onDelete(r.id)}>Delete</CButton>
                </CTableDataCell>
              </CTableRow>
            ))}
          </CTableBody>
        </CTable>
      </CCardBody>
    </CCard>
  )
}
```

**src/views/students/StudentForm.tsx**

```tsx
import React, { useEffect, useState } from 'react'
import { CCard, CCardBody, CCardHeader, CForm, CFormInput, CFormLabel, CRow, CCol, CButton } from '@coreui/react'
import { useParams, useHistory } from 'react-router-dom'
import { apiGet, apiJSON } from '../../api/client'

export default function StudentForm(){
  const params:any = useParams()
  const history = useHistory()
  const isEdit = !!params.id
  const [form, setForm] = useState<any>({ name:'', gender:'', class_name:'' })

  useEffect(()=>{ if(isEdit) apiGet(`/api/students/${params.id}`).then(res=>setForm(res.data)) }, [isEdit, params.id])

  function onChange(e:any){ setForm({...form, [e.target.name]: e.target.value}) }
  async function onSubmit(e:any){
    e.preventDefault()
    if(isEdit) await apiJSON(`/api/students/${params.id}`, 'PUT', form)
    else await apiJSON('/api/students', 'POST', form)
    history.push('/students')
  }

  return (
    <CCard>
      <CCardHeader>{isEdit ? 'Edit Student' : 'New Student'}</CCardHeader>
      <CCardBody>
        <CForm onSubmit={onSubmit}>
          <CRow className="mb-3">
            <CFormLabel className="col-sm-2 col-form-label">Name</CFormLabel>
            <CCol sm={10}><CFormInput name="name" value={form.name} onChange={onChange} required /></CCol>
          </CRow>
          <CRow className="mb-3">
            <CFormLabel className="col-sm-2 col-form-label">Gender</CFormLabel>
            <CCol sm={10}><CFormInput name="gender" value={form.gender} onChange={onChange} /></CCol>
          </CRow>
          <CRow className="mb-4">
            <CFormLabel className="col-sm-2 col-form-label">Class</CFormLabel>
            <CCol sm={10}><CFormInput name="class_name" value={form.class_name} onChange={onChange} /></CCol>
          </CRow>
          <CButton type="submit" color="primary">Save</CButton>
          <CButton type="button" color="secondary" className="ms-2" onClick={()=>history.back()}>Cancel</CButton>
        </CForm>
      </CCardBody>
    </CCard>
  )
}
```

> 课程/选课页面照此模式复用即可。

### 2.5 主题与“科技蓝”定制

CoreUI 支持 SCSS 变量与 CSS 覆盖。
 **src/scss/_custom.scss**

```scss
$primary: #1f6feb; // 科技蓝
$secondary: #6c757d;

@import "~@coreui/coreui/scss/coreui"; // 保持在覆盖变量后引入

// 适度圆角与卡片阴影
:root{
  --cui-border-radius: 1rem;
}
```

确保入口样式引入了 `_custom.scss`（参考模板 README）。

### 2.6 仪表盘图表数据

在 Flask 新增 `/api/dashboard/metrics`，返回例如：

```json
{
  "cards": { "students": 523, "teachers": 37, "courses": 68, "enrollments": 1124 },
  "series": {
    "enrollments_daily": [{"date":"2025-11-01","count":21}, ...]
  }
}
```

前端 `Dashboard.tsx` 用 CoreUI + Chart.js 渲染卡片和折线/柱状图。

------

## 第 3 步：本地运行

**窗口 1：后端**

```bash
flask run  # 默认 5000
```

**窗口 2：前端**

```bash
cd frontend
npm start  # 默认 3000
```

> 若用了 `proxy`，前端直接请求 `/api/...`；否则用 `REACT_APP_API_BASE_URL`。

------

