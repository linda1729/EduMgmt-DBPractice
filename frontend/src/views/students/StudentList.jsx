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
import { CChartBar } from '@coreui/react-chartjs'

import {
  createStudent,
  deleteStudent,
  fetchStudentMeta,
  listStudents,
  updateStudent,
} from 'src/api/students'
import PaginationControls from 'src/components/PaginationControls'

const pageSizeOptions = [10, 20, 50]

const genderOptions = [
  { label: '男 (Male)', value: 'Male' },
  { label: '女 (Female)', value: 'Female' },
  { label: '其他 (Other)', value: 'Other' },
]

const defaultCreateForm = {
  sno: '',
  name: '',
  gender: 'Male',
  enroll_year: '',
  department: '',
  birth_date: '',
  email: '',
  phone: '',
}

const StudentList = () => {
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState('')
  const [formState, setFormState] = useState({ q: '', department: '', enrollYear: '' })
  const [filters, setFilters] = useState(formState)
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(pageSizeOptions[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [createForm, setCreateForm] = useState(defaultCreateForm)
  const [rowEdits, setRowEdits] = useState({})
  const [refreshKey, setRefreshKey] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const loadMeta = async () => {
      setMetaError('')
      try {
        const data = await fetchStudentMeta()
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
        const response = await listStudents({
          page,
          perPage,
          department: filters.department || undefined,
          enrollYear: filters.enrollYear || undefined,
          keyword: filters.q || undefined,
        })
        setItems(response.items || [])
        setTotal(response.total || 0)
      } catch (err) {
        setError(err.message || '加载学生信息失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [filters, page, perPage, refreshKey])

  const deptChartData = useMemo(() => {
    const distribution = meta?.stats?.department_distribution ?? []
    if (distribution.length === 0) {
      return {
        labels: ['暂无数据'],
        datasets: [{ label: '学生数', data: [0], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels: distribution.map((item) => item.label),
      datasets: [
        {
          label: '学生数',
          borderRadius: 12,
          data: distribution.map((item) => item.value),
          backgroundColor: distribution.map((_, idx) => `hsla(${(idx * 60) % 360}, 70%, 65%, 0.85)`),
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
    const nextState = { q: '', department: '', enrollYear: '' }
    setFormState(nextState)
    setFilters(nextState)
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
      if (!createForm.sno || !createForm.name || !createForm.enroll_year) {
        throw new Error('请完整填写学号、姓名与入学年份')
      }
      const payload = {
        ...createForm,
        enroll_year: Number(createForm.enroll_year),
        department: createForm.department || null,
        birth_date: createForm.birth_date || null,
        email: createForm.email || null,
        phone: createForm.phone || null,
      }
      await createStudent(payload)
      setCreateForm(defaultCreateForm)
      setRefreshKey((prev) => prev + 1)
      setMeta((prev) =>
        prev
          ? {
              ...prev,
              stats: {
                ...prev.stats,
                total: prev.stats.total + 1,
              },
            }
          : prev,
      )
    } catch (err) {
      setError(err.message || '创建学生失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRowChange = (sno, field, value) => {
    setRowEdits((prev) => ({
      ...prev,
      [sno]: { ...prev[sno], [field]: value },
    }))
  }

  const handleSaveRow = async (student) => {
    const edits = rowEdits[student.sno] || {}
    const payload = {
      name: edits.name ?? student.name,
      gender: edits.gender ?? student.gender,
      department: edits.department ?? student.department,
      enroll_year: Number(edits.enroll_year ?? student.enroll_year),
      birth_date: edits.birth_date ?? (student.birth_date?.slice(0, 10) || null),
      email: edits.email ?? student.email,
      phone: edits.phone ?? student.phone,
    }
    try {
      await updateStudent(student.sno, payload)
      setRowEdits((prev) => {
        const next = { ...prev }
        delete next[student.sno]
        return next
      })
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '更新学生失败')
    }
  }

  const handleDelete = async (sno) => {
    if (!window.confirm('确定要删除该学生吗？')) {
      return
    }
    try {
      await deleteStudent(sno)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '删除学生失败')
    }
  }

  return (
    <>
      <CRow className="g-3 mb-4">
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">在册学生</p>
              <div className="display-6 fw-semibold">{meta?.stats?.total ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">女性学生</p>
              <div className="display-6 fw-semibold">
                {meta?.stats?.gender_distribution?.find((item) => item.label === 'Female')?.value ?? 0}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">男性学生</p>
              <div className="display-6 fw-semibold">
                {meta?.stats?.gender_distribution?.find((item) => item.label === 'Male')?.value ?? 0}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CRow className="g-4 mb-4">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>新增学生</strong>
            </CCardHeader>
            <CCardBody>
              <CForm className="row g-3" onSubmit={handleCreate}>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-sno">学号 *</CFormLabel>
                  <CFormInput id="create-sno" name="sno" value={createForm.sno} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-name">姓名 *</CFormLabel>
                  <CFormInput id="create-name" name="name" value={createForm.name} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-gender">性别 *</CFormLabel>
                  <CFormSelect id="create-gender" name="gender" value={createForm.gender} onChange={handleCreateChange}>
                    {genderOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-enroll">入学年份 *</CFormLabel>
                  <CFormInput
                    id="create-enroll"
                    name="enroll_year"
                    type="number"
                    value={createForm.enroll_year}
                    onChange={handleCreateChange}
                    required
                  />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-birth">出生日期</CFormLabel>
                  <CFormInput
                    type="date"
                    id="create-birth"
                    name="birth_date"
                    value={createForm.birth_date}
                    onChange={handleCreateChange}
                  />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-dept">所属院系</CFormLabel>
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
                  <CFormLabel htmlFor="create-email">邮箱</CFormLabel>
                  <CFormInput id="create-email" name="email" value={createForm.email} onChange={handleCreateChange} />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-phone">电话</CFormLabel>
                  <CFormInput id="create-phone" name="phone" value={createForm.phone} onChange={handleCreateChange} />
                </CCol>
                <CCol xs={12} className="text-end">
                  <CButton type="submit" color="primary" disabled={submitting}>
                    {submitting ? '提交中...' : '创建学生'}
                  </CButton>
                </CCol>
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>院系分布</strong>
            </CCardHeader>
            <CCardBody>
              {metaError && <CAlert color="danger">{metaError}</CAlert>}
              <CChartBar data={deptChartData} options={{ maintainAspectRatio: false }} style={{ height: '320px' }} />
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CCard>
        <CCardHeader className="d-flex flex-wrap justify-content-between align-items-end gap-3">
          <div>
            <h5 className="mb-0">学生列表</h5>
            <div className="text-body-secondary small">最多展示 200 名学生，可按关键字与院系过滤</div>
          </div>
          <div className="d-flex gap-2">
            <CButton color="secondary" variant="outline" onClick={resetFilters} disabled={loading}>
              重置
            </CButton>
          </div>
        </CCardHeader>
        <CCardBody>
          <CForm className="row g-3 mb-4" onSubmit={applyFilters}>
            <CCol md={4}>
              <CFormLabel htmlFor="q">关键字（姓名/学号）</CFormLabel>
              <CFormInput id="q" name="q" value={formState.q} onChange={handleFilterChange} placeholder="例如：20231234" />
            </CCol>
            <CCol md={4}>
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
            <CCol md={3}>
              <CFormLabel htmlFor="enrollYear">入学年份</CFormLabel>
              <CFormInput id="enrollYear" name="enrollYear" type="number" value={formState.enrollYear} onChange={handleFilterChange} />
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
            <div className="small text-body-secondary">共 {total} 名学生</div>
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
                  <CTableHeaderCell scope="col">学号</CTableHeaderCell>
                  <CTableHeaderCell scope="col">姓名</CTableHeaderCell>
                  <CTableHeaderCell scope="col">性别</CTableHeaderCell>
                  <CTableHeaderCell scope="col">院系</CTableHeaderCell>
                  <CTableHeaderCell scope="col">入学年份</CTableHeaderCell>
                  <CTableHeaderCell scope="col">出生日期</CTableHeaderCell>
                  <CTableHeaderCell scope="col">联系方式</CTableHeaderCell>
                  <CTableHeaderCell scope="col" className="text-end">
                    操作
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {items.map((student) => {
                  const edits = rowEdits[student.sno] || {}
                  return (
                    <CTableRow key={student.sno}>
                      <CTableDataCell className="fw-semibold">{student.sno}</CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          value={edits.name ?? student.name}
                          onChange={(event) => handleRowChange(student.sno, 'name', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.gender ?? student.gender}
                          onChange={(event) => handleRowChange(student.sno, 'gender', event.target.value)}
                        >
                          {genderOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.department ?? student.department ?? ''}
                          onChange={(event) => handleRowChange(student.sno, 'department', event.target.value)}
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
                        <CFormInput
                          size="sm"
                          type="number"
                          value={edits.enroll_year ?? student.enroll_year}
                          onChange={(event) => handleRowChange(student.sno, 'enroll_year', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          type="date"
                          value={edits.birth_date ?? student.birth_date?.slice(0, 10) ?? ''}
                          onChange={(event) => handleRowChange(student.sno, 'birth_date', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <div className="d-flex flex-column gap-2">
                          <CFormInput
                            size="sm"
                            type="email"
                            placeholder="邮箱"
                            value={edits.email ?? student.email ?? ''}
                            onChange={(event) => handleRowChange(student.sno, 'email', event.target.value)}
                          />
                          <CFormInput
                            size="sm"
                            placeholder="电话"
                            value={edits.phone ?? student.phone ?? ''}
                            onChange={(event) => handleRowChange(student.sno, 'phone', event.target.value)}
                          />
                        </div>
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        <div className="d-flex justify-content-end gap-2">
                          <CButton size="sm" color="primary" variant="outline" onClick={() => handleSaveRow(student)}>
                            保存
                          </CButton>
                          <CButton size="sm" color="danger" variant="outline" onClick={() => handleDelete(student.sno)}>
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
              <div className="text-center py-5 text-body-secondary">暂无数据</div>
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

export default StudentList
