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
  createEnrollment,
  deleteEnrollment,
  fetchEnrollmentMeta,
  listEnrollments,
  updateEnrollment,
} from 'src/api/enrollments'
import PaginationControls from 'src/components/PaginationControls'

const pageSizeOptions = [10, 20, 50]

const EnrollmentList = () => {
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState('')
  const [formState, setFormState] = useState({ student: '', course: '', status: '', year: '', term: '' })
  const [filters, setFilters] = useState(formState)
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(pageSizeOptions[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [refreshKey, setRefreshKey] = useState(0)
  const [rowEdits, setRowEdits] = useState({})
  const [createForm, setCreateForm] = useState({
    student_id: '',
    course_id: '',
    year: '',
    term: '',
    status: 'enrolled',
    grade: '',
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const loadMeta = async () => {
      setMetaError('')
      try {
        const data = await fetchEnrollmentMeta()
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
        const response = await listEnrollments({
          page,
          perPage,
          student: filters.student || undefined,
          course: filters.course || undefined,
          status: filters.status || undefined,
          year: filters.year || undefined,
          term: filters.term || undefined,
        })
        setItems(response.items || [])
        setTotal(response.total || 0)
      } catch (err) {
        setError(err.message || '加载选课失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [filters, page, perPage, refreshKey])

  const chartData = useMemo(() => {
    const distribution = meta?.stats?.status_distribution ?? []
    if (distribution.length === 0) {
      return {
        labels: ['暂无'],
        datasets: [{ data: [1], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels: distribution.map((item) => item.label),
      datasets: [
        {
          data: distribution.map((item) => item.value),
          backgroundColor: ['#0ea5e9', '#10b981', '#f97316', '#f43f5e'],
        },
      ],
    }
  }, [meta])

  const handleFilterChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const applyFilters = (event) => {
    event.preventDefault()
    setFilters(formState)
    setPage(1)
  }

  const resetFilters = () => {
    const next = { student: '', course: '', status: '', year: '', term: '' }
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
    setSubmitting(true)
    setError('')
    try {
      if (!createForm.student_id || !createForm.course_id || !createForm.year || !createForm.term) {
        throw new Error('请填写学生、课程、学年与学期')
      }
      const payload = {
        ...createForm,
        year: Number(createForm.year),
        grade: createForm.grade ? Number(createForm.grade) : null,
      }
      await createEnrollment(payload)
      setCreateForm({
        student_id: '',
        course_id: '',
        year: '',
        term: '',
        status: 'enrolled',
        grade: '',
      })
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '新建选课失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRowChange = (id, field, value) => {
    setRowEdits((prev) => ({
      ...prev,
      [id]: { ...prev[id], [field]: value },
    }))
  }

  const handleSaveRow = async (item) => {
    const key = `${item.student_id}-${item.course_id}`
    const edits = rowEdits[key] || {}
    const payload = {
      status: edits.status ?? item.status,
      grade: edits.grade === '' ? null : Number(edits.grade ?? item.grade ?? ''),
      year: edits.year ?? item.year,
      term: edits.term ?? item.term,
    }
    try {
      await updateEnrollment(item.student_id, item.course_id, payload)
      setRowEdits((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '更新选课失败')
    }
  }

  const handleDelete = async (sno, cno) => {
    if (!window.confirm(`确定删除选课 ${sno} - ${cno} 吗？`)) {
      return
    }
    try {
      await deleteEnrollment(sno, cno)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '删除失败')
    }
  }

  const formatDateTime = (value) => {
    if (!value) return '-'
    try {
      const date = new Date(value)
      return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    } catch (err) {
      return value
    }
  }

  return (
    <>
      <CRow className="g-3 mb-4">
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">选课记录</p>
              <div className="display-6 fw-semibold">{meta?.stats?.total ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">已完成</p>
              <div className="display-6 fw-semibold">
                {meta?.stats?.status_distribution?.find((item) => item.label === 'completed')?.value ?? 0}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">正在选课</p>
              <div className="display-6 fw-semibold">
                {meta?.stats?.status_distribution?.find((item) => item.label === 'enrolled')?.value ?? 0}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CRow className="g-4 mb-4">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>新增选课记录</strong>
            </CCardHeader>
            <CCardBody>
              <CForm className="row g-3" onSubmit={handleCreate}>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-student">学生 *</CFormLabel>
                  <CFormSelect id="create-student" name="student_id" value={createForm.student_id} onChange={handleCreateChange} required>
                    <option value="">请选择学生</option>
                    {(meta?.students || []).map((student) => (
                      <option key={student.sno} value={student.sno}>
                        {student.sno} · {student.sname}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-course">课程 *</CFormLabel>
                  <CFormSelect id="create-course" name="course_id" value={createForm.course_id} onChange={handleCreateChange} required>
                    <option value="">请选择课程</option>
                    {(meta?.courses || []).map((course) => (
                      <option key={course.cno} value={course.cno}>
                        {course.cno} · {course.cname}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-year">学年 *</CFormLabel>
                  <CFormInput
                    id="create-year"
                    name="year"
                    type="number"
                    value={createForm.year}
                    onChange={handleCreateChange}
                    required
                  />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-term">学期 *</CFormLabel>
                  <CFormSelect id="create-term" name="term" value={createForm.term} onChange={handleCreateChange} required>
                    <option value="">请选择学期</option>
                    {(meta?.terms || []).map((term) => (
                      <option key={term.term_code} value={term.term_code}>
                        {term.term_name}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-status">状态</CFormLabel>
                  <CFormSelect id="create-status" name="status" value={createForm.status} onChange={handleCreateChange}>
                    {(meta?.statuses || []).map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-grade">成绩</CFormLabel>
                  <CFormInput
                    id="create-grade"
                    name="grade"
                    type="number"
                    step="0.01"
                    value={createForm.grade}
                    onChange={handleCreateChange}
                  />
                </CCol>
                <CCol xs={12} className="text-end">
                  <CButton color="primary" type="submit" disabled={submitting}>
                    {submitting ? '提交中...' : '创建选课记录'}
                  </CButton>
                </CCol>
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>状态分布</strong>
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
            <h5 className="mb-0">选课列表</h5>
            <div className="text-body-secondary small">最多展示 300 条选课记录，可按学生、课程、状态、学期等组合筛选</div>
          </div>
          <CButton color="secondary" variant="outline" onClick={resetFilters} disabled={loading}>
            重置
          </CButton>
        </CCardHeader>
        <CCardBody>
          <CForm className="row g-3 mb-4" onSubmit={applyFilters}>
            <CCol md={3}>
              <CFormLabel htmlFor="student">学生学号</CFormLabel>
              <CFormInput
                id="student"
                name="student"
                value={formState.student}
                onChange={handleFilterChange}
                placeholder="输入学号，例如：20230001"
                list="student-options"
              />
              <datalist id="student-options">
                {(meta?.students || []).map((student) => (
                  <option key={student.sno} value={student.sno}>
                    {student.sname}
                  </option>
                ))}
              </datalist>
            </CCol>
            <CCol md={3}>
              <CFormLabel htmlFor="course">课程编号</CFormLabel>
              <CFormInput
                id="course"
                name="course"
                value={formState.course}
                onChange={handleFilterChange}
                placeholder="输入课程号，例如：CS001"
                list="course-options"
              />
              <datalist id="course-options">
                {(meta?.courses || []).map((course) => (
                  <option key={course.cno} value={course.cno}>
                    {course.cname}
                  </option>
                ))}
              </datalist>
            </CCol>
            <CCol md={2}>
              <CFormLabel htmlFor="status">状态</CFormLabel>
              <CFormSelect id="status" name="status" value={formState.status} onChange={handleFilterChange}>
                <option value="">全部</option>
                {(meta?.statuses || []).map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={2}>
              <CFormLabel htmlFor="year">学年</CFormLabel>
              <CFormInput id="year" name="year" type="number" value={formState.year} onChange={handleFilterChange} />
            </CCol>
            <CCol md={2}>
              <CFormLabel htmlFor="term">学期</CFormLabel>
              <CFormSelect id="term" name="term" value={formState.term} onChange={handleFilterChange}>
                <option value="">全部</option>
                {(meta?.terms || []).map((term) => (
                  <option key={term.term_code} value={term.term_code}>
                    {term.term_name}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol xs={12} className="d-flex justify-content-end">
              <CButton type="submit" color="primary" disabled={loading}>
                查询
              </CButton>
            </CCol>
          </CForm>

          {error && (
            <CAlert color="danger" className="mb-4">
              {error}
            </CAlert>
          )}

          <div className="d-flex justify-content-between flex-wrap align-items-center gap-3 mb-3">
            <div className="small text-body-secondary">共 {total} 条记录</div>
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
            <CTable hover align="middle">
              <CTableHead color="light">
                <CTableRow>
                  <CTableHeaderCell scope="col">学生</CTableHeaderCell>
                  <CTableHeaderCell scope="col">课程</CTableHeaderCell>
                  <CTableHeaderCell scope="col">学年</CTableHeaderCell>
                  <CTableHeaderCell scope="col">学期</CTableHeaderCell>
                  <CTableHeaderCell scope="col">状态</CTableHeaderCell>
                  <CTableHeaderCell scope="col">成绩</CTableHeaderCell>
                  <CTableHeaderCell scope="col">选课时间</CTableHeaderCell>
                  <CTableHeaderCell scope="col" className="text-end">
                    操作
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {items.map((item) => {
                  const key = `${item.student_id}-${item.course_id}`
                  const edits = rowEdits[key] || {}
                  return (
                    <CTableRow key={key}>
                      <CTableDataCell>
                        <div className="fw-semibold">{item.student_id}</div>
                      </CTableDataCell>
                      <CTableDataCell>
                        <div className="fw-semibold">{item.course_id}</div>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          type="number"
                          value={edits.year ?? item.year ?? ''}
                          onChange={(event) => handleRowChange(key, 'year', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.term ?? item.term ?? ''}
                          onChange={(event) => handleRowChange(key, 'term', event.target.value)}
                        >
                          {(meta?.terms || []).map((term) => (
                            <option key={term.term_code} value={term.term_code}>
                              {term.term_name}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.status ?? item.status}
                          onChange={(event) => handleRowChange(key, 'status', event.target.value)}
                        >
                          {(meta?.statuses || []).map((status) => (
                            <option key={status} value={status}>
                              {status}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          type="number"
                          step="0.01"
                          value={edits.grade ?? (item.grade ?? '')}
                          onChange={(event) => handleRowChange(key, 'grade', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>{formatDateTime(item.enroll_date)}</CTableDataCell>
                      <CTableDataCell className="text-end">
                        <div className="d-flex justify-content-end gap-2">
                          <CButton size="sm" color="primary" variant="outline" onClick={() => handleSaveRow(item)}>
                            保存
                          </CButton>
                          <CButton size="sm" color="danger" variant="outline" onClick={() => handleDelete(item.student_id, item.course_id)}>
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
              <div className="text-center py-5 text-body-secondary">暂无选课记录</div>
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

export default EnrollmentList
