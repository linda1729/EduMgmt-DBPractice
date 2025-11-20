import React, { useEffect, useMemo, useState } from 'react'
import {
  CAlert,
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
import { CChartBar } from '@coreui/react-chartjs'

import {
  createTeaching,
  deleteTeaching,
  fetchTeachingMeta,
  listTeachings,
  updateTeaching,
} from 'src/api/teachings'
import PaginationControls from 'src/components/PaginationControls'

const pageSizeOptions = [10, 20, 50]

const defaultCreateState = {
  course_id: '',
  teacher_id: '',
  year: '',
  term: '',
  room_id: '',
  capacity: '',
  start_date: '',
  end_date: '',
}

const TeachingList = () => {
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState('')
  const [formState, setFormState] = useState({ course: '', teacher: '', term: '', year: '' })
  const [filters, setFilters] = useState(formState)
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(pageSizeOptions[0])
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [rowEdits, setRowEdits] = useState({})
  const [createForm, setCreateForm] = useState(defaultCreateState)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    const loadMeta = async () => {
      setMetaError('')
      try {
        const data = await fetchTeachingMeta()
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
        const response = await listTeachings({
          page,
          perPage,
          course: filters.course || undefined,
          teacher: filters.teacher || undefined,
          term: filters.term || undefined,
          year: filters.year || undefined,
        })
        setItems(response.items || [])
        setTotal(response.total || 0)
      } catch (err) {
        setError(err.message || '加载授课安排失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [filters, page, perPage, refreshKey])

  const termChartData = useMemo(() => {
    const distribution = meta?.stats?.term_distribution ?? []
    if (distribution.length === 0) {
      return {
        labels: ['暂无数据'],
        datasets: [{ label: '授课次数', data: [0], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels: distribution.map((item) => item.label),
      datasets: [
        {
          label: '授课次数',
          data: distribution.map((item) => item.value),
          backgroundColor: distribution.map((_, idx) => `hsla(${(idx * 90) % 360}, 65%, 60%, 0.85)`),
          borderRadius: 12,
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
    const next = { course: '', teacher: '', term: '', year: '' }
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
      if (!createForm.course_id || !createForm.teacher_id || !createForm.year || !createForm.term) {
        throw new Error('请填写课程、教师、学年与学期')
      }
      await createTeaching({
        course_id: createForm.course_id,
        teacher_id: createForm.teacher_id,
        year: Number(createForm.year),
        term: createForm.term,
        room_id: createForm.room_id || null,
        capacity: createForm.capacity ? Number(createForm.capacity) : undefined,
        start_date: createForm.start_date || null,
        end_date: createForm.end_date || null,
      })
      setCreateForm(defaultCreateState)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '创建授课安排失败')
    } finally {
      setCreating(false)
    }
  }

  const handleRowChange = (teachId, field, value) => {
    setRowEdits((prev) => ({
      ...prev,
      [teachId]: { ...prev[teachId], [field]: value },
    }))
  }

  const handleSaveRow = async (teaching) => {
    const edits = rowEdits[teaching.teach_id] || {}
    const payload = {}
    if (edits.course_id !== undefined) payload.course_id = edits.course_id
    if (edits.teacher_id !== undefined) payload.teacher_id = edits.teacher_id
    if (edits.year !== undefined) payload.year = Number(edits.year)
    if (edits.term !== undefined) payload.term = edits.term
    if (edits.room_id !== undefined) payload.room_id = edits.room_id || null
    if (edits.capacity !== undefined) payload.capacity = edits.capacity ? Number(edits.capacity) : null
    if (edits.start_date !== undefined) payload.start_date = edits.start_date || null
    if (edits.end_date !== undefined) payload.end_date = edits.end_date || null
    try {
      await updateTeaching(teaching.teach_id, payload)
      setRowEdits((prev) => {
        const next = { ...prev }
        delete next[teaching.teach_id]
        return next
      })
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '更新授课安排失败')
    }
  }

  const handleDelete = async (teachId) => {
    if (!window.confirm(`确认删除授课安排 ${teachId} 吗？`)) {
      return
    }
    try {
      await deleteTeaching(teachId)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '删除授课安排失败')
    }
  }

  return (
    <>
      <CRow className="g-3 mb-4">
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">授课安排</p>
              <div className="display-6 fw-semibold">{meta?.stats?.total ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">开课学期数</p>
              <div className="display-6 fw-semibold">{meta?.stats?.term_distribution?.length ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">平均容量</p>
              <div className="display-6 fw-semibold">{meta?.stats?.average_capacity ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CRow className="g-4 mb-4">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>新增授课安排</strong>
            </CCardHeader>
            <CCardBody>
              <CForm className="row g-3" onSubmit={handleCreate}>
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
                  <CFormLabel htmlFor="create-teacher">教师 *</CFormLabel>
                  <CFormSelect id="create-teacher" name="teacher_id" value={createForm.teacher_id} onChange={handleCreateChange} required>
                    <option value="">请选择教师</option>
                    {(meta?.teachers || []).map((teacher) => (
                      <option key={teacher.tno} value={teacher.tno}>
                        {teacher.tno} · {teacher.tname}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-year">开课年份 *</CFormLabel>
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
                  <CFormLabel htmlFor="create-room">教室</CFormLabel>
                  <CFormSelect id="create-room" name="room_id" value={createForm.room_id} onChange={handleCreateChange}>
                    <option value="">未指定</option>
                    {(meta?.classrooms || []).map((room) => (
                      <option key={room.room_id} value={room.room_id}>
                        {room.label}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-capacity">容量</CFormLabel>
                  <CFormInput
                    id="create-capacity"
                    name="capacity"
                    type="number"
                    value={createForm.capacity}
                    onChange={handleCreateChange}
                  />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-start">开始日期</CFormLabel>
                  <CFormInput id="create-start" name="start_date" type="date" value={createForm.start_date} onChange={handleCreateChange} />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-end">结束日期</CFormLabel>
                  <CFormInput id="create-end" name="end_date" type="date" value={createForm.end_date} onChange={handleCreateChange} />
                </CCol>
                <CCol xs={12} className="text-end">
                  <CButton type="submit" color="primary" disabled={creating}>
                    {creating ? '提交中...' : '创建授课安排'}
                  </CButton>
                </CCol>
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>学期分布</strong>
            </CCardHeader>
            <CCardBody>
              {metaError && <CAlert color="danger">{metaError}</CAlert>}
              <CChartBar data={termChartData} options={{ maintainAspectRatio: false }} style={{ height: '320px' }} />
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CCard>
        <CCardHeader className="d-flex flex-wrap justify-content-between align-items-end gap-3">
          <div>
            <h5 className="mb-0">授课安排列表</h5>
            <div className="text-body-secondary small">掌握课程、教师、教室的排课信息</div>
          </div>
          <CButton color="secondary" variant="outline" onClick={resetFilters} disabled={loading}>
            重置
          </CButton>
        </CCardHeader>
        <CCardBody>
          <CForm className="row g-3 mb-4" onSubmit={applyFilters}>
            <CCol md={3}>
              <CFormLabel htmlFor="course">课程编号</CFormLabel>
              <CFormInput
                id="course"
                name="course"
                value={formState.course}
                onChange={handleFilterChange}
                placeholder="输入课程号"
                list="teaching-course-options"
              />
              <datalist id="teaching-course-options">
                {(meta?.courses || []).map((course) => (
                  <option key={course.cno} value={course.cno}>
                    {course.cname}
                  </option>
                ))}
              </datalist>
            </CCol>
            <CCol md={3}>
              <CFormLabel htmlFor="teacher">教师工号</CFormLabel>
              <CFormInput
                id="teacher"
                name="teacher"
                value={formState.teacher}
                onChange={handleFilterChange}
                placeholder="输入教师工号"
                list="teaching-teacher-options"
              />
              <datalist id="teaching-teacher-options">
                {(meta?.teachers || []).map((teacher) => (
                  <option key={teacher.tno} value={teacher.tno}>
                    {teacher.tname}
                  </option>
                ))}
              </datalist>
            </CCol>
            <CCol md={2}>
              <CFormLabel htmlFor="term">学期</CFormLabel>
              <CFormSelect id="term" name="term" value={formState.term} onChange={handleFilterChange}>
                <option value="">全部学期</option>
                {(meta?.terms || []).map((term) => (
                  <option key={term.term_code} value={term.term_code}>
                    {term.term_name}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={2}>
              <CFormLabel htmlFor="year">学年</CFormLabel>
              <CFormInput id="year" name="year" type="number" value={formState.year} onChange={handleFilterChange} />
            </CCol>
            <CCol md={1} className="d-flex align-items-end">
              <CButton type="submit" color="primary" className="w-100" disabled={loading}>
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
                  <CTableHeaderCell scope="col">课程</CTableHeaderCell>
                  <CTableHeaderCell scope="col">教师</CTableHeaderCell>
                  <CTableHeaderCell scope="col">学年/学期</CTableHeaderCell>
                  <CTableHeaderCell scope="col">教室</CTableHeaderCell>
                  <CTableHeaderCell scope="col">容量</CTableHeaderCell>
                  <CTableHeaderCell scope="col">起止日期</CTableHeaderCell>
                  <CTableHeaderCell scope="col" className="text-end">
                    操作
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {items.map((item) => {
                  const edits = rowEdits[item.teach_id] || {}
                  return (
                    <CTableRow key={item.teach_id}>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.course_id ?? item.course_id}
                          onChange={(event) => handleRowChange(item.teach_id, 'course_id', event.target.value)}
                        >
                          {(meta?.courses || []).map((course) => (
                            <option key={course.cno} value={course.cno}>
                              {course.cno} · {course.cname}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.teacher_id ?? item.teacher_id}
                          onChange={(event) => handleRowChange(item.teach_id, 'teacher_id', event.target.value)}
                        >
                          {(meta?.teachers || []).map((teacher) => (
                            <option key={teacher.tno} value={teacher.tno}>
                              {teacher.tno} · {teacher.tname}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <div className="d-flex gap-2">
                          <CFormInput
                            size="sm"
                            type="number"
                            value={edits.year ?? item.year ?? ''}
                            onChange={(event) => handleRowChange(item.teach_id, 'year', event.target.value)}
                          />
                          <CFormSelect
                            size="sm"
                            value={edits.term ?? item.term ?? ''}
                            onChange={(event) => handleRowChange(item.teach_id, 'term', event.target.value)}
                          >
                            {(meta?.terms || []).map((term) => (
                              <option key={term.term_code} value={term.term_code}>
                                {term.term_name}
                              </option>
                            ))}
                          </CFormSelect>
                        </div>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.room_id ?? item.room_id ?? ''}
                          onChange={(event) => handleRowChange(item.teach_id, 'room_id', event.target.value)}
                        >
                          <option value="">未指定</option>
                          {(meta?.classrooms || []).map((room) => (
                            <option key={room.room_id} value={room.room_id}>
                              {room.label}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          type="number"
                          value={edits.capacity ?? item.capacity ?? ''}
                          onChange={(event) => handleRowChange(item.teach_id, 'capacity', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <div className="d-flex flex-column gap-2">
                          <CFormInput
                            size="sm"
                            type="date"
                            value={edits.start_date ?? item.start_date ?? ''}
                            onChange={(event) => handleRowChange(item.teach_id, 'start_date', event.target.value)}
                          />
                          <CFormInput
                            size="sm"
                            type="date"
                            value={edits.end_date ?? item.end_date ?? ''}
                            onChange={(event) => handleRowChange(item.teach_id, 'end_date', event.target.value)}
                          />
                        </div>
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        <div className="d-flex justify-content-end gap-2">
                          <CButton size="sm" color="primary" variant="outline" onClick={() => handleSaveRow(item)}>
                            保存
                          </CButton>
                          <CButton size="sm" color="danger" variant="outline" onClick={() => handleDelete(item.teach_id)}>
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
              <div className="text-center py-5 text-body-secondary">暂无授课安排</div>
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

export default TeachingList
