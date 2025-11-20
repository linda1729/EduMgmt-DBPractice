import React, { useEffect, useMemo, useState } from 'react'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormCheck,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import { CChartDoughnut } from '@coreui/react-chartjs'

import {
  createCourse,
  deleteCourse,
  fetchCourseMeta,
  listCourses,
  updateCourse,
} from 'src/api/courses'
import PaginationControls from 'src/components/PaginationControls'

const pageSizeOptions = [10, 20, 50]

const defaultCreateState = {
  cno: '',
  name: '',
  credits: '',
  hours: '',
  department: '',
  prerequisite: '',
  is_active: true,
}

const CourseList = () => {
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState('')
  const [formState, setFormState] = useState({ q: '', department: '', includeInactive: false })
  const [filters, setFilters] = useState(formState)
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(pageSizeOptions[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [refreshKey, setRefreshKey] = useState(0)
  const [rowEdits, setRowEdits] = useState({})
  const [createForm, setCreateForm] = useState(defaultCreateState)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    const loadMeta = async () => {
      setMetaError('')
      try {
        const data = await fetchCourseMeta()
        setMeta(data)
      } catch (err) {
        setMetaError(err.message || '加载统计信息失败')
      }
    }
    loadMeta()
  }, [])

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await listCourses({
          page,
          perPage,
          department: filters.department || undefined,
          keyword: filters.q || undefined,
          includeInactive: Boolean(filters.includeInactive),
        })
        setItems(response.items || [])
        setTotal(response.total || 0)
      } catch (err) {
        setError(err.message || '加载课程失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [filters, page, perPage, refreshKey])

  const chartData = useMemo(() => {
    const distribution = meta?.stats?.department_distribution ?? []
    if (distribution.length === 0) {
      return {
        labels: ['暂无数据'],
        datasets: [{ data: [1], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels: distribution.map((item) => item.label),
      datasets: [
        {
          data: distribution.map((item) => item.value),
          backgroundColor: distribution.map((_, idx) => `hsla(${(idx * 70) % 360}, 70%, 60%, 0.85)`),
        },
      ],
    }
  }, [meta])

  const handleFilterChange = (event) => {
    const { name, value, type, checked } = event.target
    setFormState((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const applyFilters = (event) => {
    event.preventDefault()
    setFilters(formState)
    setPage(1)
  }

  const resetFilters = () => {
    const next = { q: '', department: '', includeInactive: false }
    setFormState(next)
    setFilters(next)
    setPage(1)
  }

  const handleCreateChange = (event) => {
    const { name, value } = event.target
    setCreateForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleCreate = async (event) => {
    event.preventDefault()
    setCreating(true)
    setError('')
    try {
      if (!createForm.cno || !createForm.name || !createForm.credits || !createForm.hours) {
        throw new Error('请填写完整的课程号、名称、学分与学时')
      }
      const payload = {
        cno: createForm.cno,
        name: createForm.name,
        credits: Number(createForm.credits),
        hours: Number(createForm.hours),
        department: createForm.department || null,
        prerequisite: createForm.prerequisite || null,
        is_active: createForm.is_active,
      }
      await createCourse(payload)
      setCreateForm(defaultCreateState)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '新建课程失败')
    } finally {
      setCreating(false)
    }
  }

  const handleRowChange = (cno, field, value) => {
    setRowEdits((prev) => ({
      ...prev,
      [cno]: { ...prev[cno], [field]: value },
    }))
  }

  const handleSaveRow = async (course) => {
    const edits = rowEdits[course.cno] || {}
    const payload = {
      name: edits.name ?? course.name,
      credits: Number(edits.credits ?? course.credits),
      hours: Number(edits.hours ?? course.hours),
      department: edits.department ?? course.department,
      prerequisite: edits.prerequisite ?? course.prerequisite,
      is_active: edits.is_active ?? course.is_active,
    }
    try {
      await updateCourse(course.cno, payload)
      setRowEdits((prev) => {
        const next = { ...prev }
        delete next[course.cno]
        return next
      })
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '更新课程失败')
    }
  }

  const handleDelete = async (cno) => {
    if (!window.confirm(`确认删除课程 ${cno} ？`)) {
      return
    }
    try {
      await deleteCourse(cno)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '删除课程失败')
    }
  }

  return (
    <>
      <CRow className="g-3 mb-4">
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">课程总数</p>
              <div className="display-6 fw-semibold">{meta?.stats?.total ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">启用课程</p>
              <div className="display-6 fw-semibold">{meta?.stats?.active ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">平均学分</p>
              <div className="display-6 fw-semibold">{meta?.stats?.average_credit ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CRow className="g-4 mb-4">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>新增课程</strong>
            </CCardHeader>
            <CCardBody>
              <CForm className="row g-3" onSubmit={handleCreate}>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-cno">课程号 *</CFormLabel>
                  <CFormInput id="create-cno" name="cno" value={createForm.cno} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-name">课程名称 *</CFormLabel>
                  <CFormInput id="create-name" name="name" value={createForm.name} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-credits">学分 *</CFormLabel>
                  <CFormInput
                    id="create-credits"
                    name="credits"
                    type="number"
                    value={createForm.credits}
                    onChange={handleCreateChange}
                    required
                  />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-hours">学时 *</CFormLabel>
                  <CFormInput
                    id="create-hours"
                    name="hours"
                    type="number"
                    value={createForm.hours}
                    onChange={handleCreateChange}
                    required
                  />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-dept">开课院系</CFormLabel>
                  <CFormSelect id="create-dept" name="department" value={createForm.department} onChange={handleCreateChange}>
                    <option value="">未指定</option>
                    {(meta?.departments || []).map((dept) => (
                      <option key={dept.dno} value={dept.dno}>
                        {dept.dname}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-prereq">先修课</CFormLabel>
                  <CFormSelect
                    id="create-prereq"
                    name="prerequisite"
                    value={createForm.prerequisite}
                    onChange={handleCreateChange}
                  >
                    <option value="">无</option>
                    {(meta?.courses || []).map((course) => (
                      <option key={course.cno} value={course.cno}>
                        {course.cno} · {course.cname}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-active">状态</CFormLabel>
                  <CFormSelect
                    id="create-active"
                    name="is_active"
                    value={createForm.is_active ? 'true' : 'false'}
                    onChange={(event) => handleCreateChange({ target: { name: 'is_active', value: event.target.value === 'true' } })}
                  >
                    <option value="true">启用</option>
                    <option value="false">停用</option>
                  </CFormSelect>
                </CCol>
                <CCol xs={12} className="text-end">
                  <CButton type="submit" color="primary" disabled={creating}>
                    {creating ? '提交中...' : '创建课程'}
                  </CButton>
                </CCol>
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>院系课程数量</strong>
            </CCardHeader>
            <CCardBody>
              {metaError && <CAlert color="danger">{metaError}</CAlert>}
              <CChartDoughnut
                data={chartData}
                options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }}
                style={{ height: '320px' }}
              />
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CCard>
        <CCardHeader className="d-flex flex-wrap justify-content-between align-items-end gap-3">
          <div>
            <h5 className="mb-0">课程列表</h5>
            <div className="text-body-secondary small">支持关键字、院系与状态筛选</div>
          </div>
          <CButton color="secondary" variant="outline" onClick={resetFilters} disabled={loading}>
            重置
          </CButton>
        </CCardHeader>
        <CCardBody>
          <CForm className="row g-3 mb-4" onSubmit={applyFilters}>
            <CCol md={4}>
              <CFormLabel htmlFor="q">关键字（课程号/名称）</CFormLabel>
              <CFormInput id="q" name="q" value={formState.q} onChange={handleFilterChange} />
            </CCol>
            <CCol md={3}>
              <CFormLabel htmlFor="department">院系</CFormLabel>
              <CFormSelect id="department" name="department" value={formState.department} onChange={handleFilterChange}>
                <option value="">全部院系</option>
                {(meta?.departments || []).map((dept) => (
                  <option key={dept.dno} value={dept.dno}>
                    {dept.dname}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={3} className="d-flex align-items-end">
              <CFormCheck
                id="includeInactive"
                name="includeInactive"
                label="展示停开课程"
                checked={formState.includeInactive}
                onChange={handleFilterChange}
              />
            </CCol>
            <CCol md={2} className="d-flex align-items-end">
              <CButton type="submit" color="primary" className="w-100" disabled={loading}>
                查询
              </CButton>
            </CCol>
          </CForm>

          {error && (
            <CAlert color='danger' className="mb-4">
              {error}
            </CAlert>
          )}

          <div className="d-flex justify-content-between flex-wrap align-items-center gap-3 mb-3">
            <div className="small text-body-secondary">共 {total} 门课程</div>
            <CFormSelect
              value={perPage}
              onChange={(event) => {
                setPerPage(Number(event.target.value))
                setPage(1)
              }}
              style={{ width: '120px' }}
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  每页 {size}
                </option>
              ))}
            </CFormSelect>
          </div>

          <div className="table-responsive">
            <CTable align="middle" hover>
              <CTableHead color="light">
                <CTableRow>
                  <CTableHeaderCell scope="col">课程号</CTableHeaderCell>
                  <CTableHeaderCell scope="col">名称</CTableHeaderCell>
                  <CTableHeaderCell scope="col">学分</CTableHeaderCell>
                  <CTableHeaderCell scope="col">学时</CTableHeaderCell>
                  <CTableHeaderCell scope="col">院系</CTableHeaderCell>
                  <CTableHeaderCell scope="col">先修课</CTableHeaderCell>
                  <CTableHeaderCell scope="col">状态</CTableHeaderCell>
                  <CTableHeaderCell scope="col" className="text-end">
                    操作
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {items.map((course) => {
                  const edits = rowEdits[course.cno] || {}
                  return (
                    <CTableRow key={course.cno}>
                      <CTableDataCell className="fw-semibold">{course.cno}</CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          value={edits.name ?? course.name}
                          onChange={(event) => handleRowChange(course.cno, 'name', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          type="number"
                          value={edits.credits ?? course.credits}
                          onChange={(event) => handleRowChange(course.cno, 'credits', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          type="number"
                          value={edits.hours ?? course.hours}
                          onChange={(event) => handleRowChange(course.cno, 'hours', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.department ?? course.department ?? ''}
                          onChange={(event) => handleRowChange(course.cno, 'department', event.target.value)}
                        >
                          <option value="">未指定</option>
                          {(meta?.departments || []).map((dept) => (
                            <option key={dept.dno} value={dept.dno}>
                              {dept.dname}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.prerequisite ?? course.prerequisite ?? ''}
                          onChange={(event) => handleRowChange(course.cno, 'prerequisite', event.target.value)}
                        >
                          <option value="">无</option>
                          {(meta?.courses || []).map((option) => (
                            <option key={option.cno} value={option.cno}>
                              {option.cno} · {option.cname}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={String(edits.is_active ?? course.is_active)}
                          onChange={(event) => handleRowChange(course.cno, 'is_active', event.target.value === 'true')}
                        >
                          <option value="true">启用</option>
                          <option value="false">停用</option>
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        <div className="d-flex justify-content-end gap-2">
                          <CButton size="sm" color="primary" variant="outline" onClick={() => handleSaveRow(course)}>
                            保存
                          </CButton>
                          <CButton size="sm" color="danger" variant="outline" onClick={() => handleDelete(course.cno)}>
                            删除
                          </CButton>
                        </div>
                      </CTableDataCell>
                    </CTableRow>
                  )
                })}
              </CTableBody>
            </CTable>
            {!loading && items.length === 0 && (
              <div className="text-center py-5 text-body-secondary">暂无课程</div>
            )}
          </div>

          {loading && (
            <div className="text-center py-4">
              <CSpinner color="primary" />
            </div>
          )}

          {total > 0 && (
            <PaginationControls page={page} perPage={perPage} total={total} onPageChange={setPage} />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default CourseList
