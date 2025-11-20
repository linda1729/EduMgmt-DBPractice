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
  createTeacher,
  deleteTeacher,
  fetchTeacherMeta,
  listTeachers,
  updateTeacher,
} from 'src/api/teachers'
import PaginationControls from 'src/components/PaginationControls'

const pageSizeOptions = [10, 20, 50]

const defaultCreateState = {
  tno: '',
  name: '',
  title: '',
  department: '',
  email: '',
  phone: '',
}

const defaultFilterState = { name: '', email: '', phone: '', department: '', title: '' }

const TeacherList = () => {
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState('')
  const [formState, setFormState] = useState(() => ({ ...defaultFilterState }))
  const [filters, setFilters] = useState(() => ({ ...defaultFilterState }))
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
        const data = await fetchTeacherMeta()
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
        const response = await listTeachers({
          page,
          perPage,
          department: filters.department || undefined,
          title: filters.title || undefined,
          name: filters.name || undefined,
          email: filters.email || undefined,
          phone: filters.phone || undefined,
        })
        setItems(response.items || [])
        setTotal(response.total || 0)
      } catch (err) {
        setError(err.message || '加载教师失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [filters, page, perPage, refreshKey])

  const chartData = useMemo(() => {
    const distribution = meta?.stats?.title_distribution ?? []
    if (distribution.length === 0) {
      return {
        labels: ['暂无数据'],
        datasets: [{ label: '人数', data: [0], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels: distribution.map((item) => item.label),
      datasets: [
        {
          label: '人数',
          data: distribution.map((item) => item.value),
          backgroundColor: distribution.map((_, idx) => `hsla(${(idx * 70) % 360}, 70%, 60%, 0.85)`),
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
    const next = { ...defaultFilterState }
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
      if (!createForm.tno || !createForm.name || !createForm.title) {
        throw new Error('请填写工号、姓名与职称')
      }
      await createTeacher({
        tno: createForm.tno,
        name: createForm.name,
        title: createForm.title,
        department: createForm.department || null,
        email: createForm.email || null,
        phone: createForm.phone || null,
      })
      setCreateForm(defaultCreateState)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '创建教师失败')
    } finally {
      setCreating(false)
    }
  }

  const handleRowChange = (tno, field, value) => {
    setRowEdits((prev) => ({
      ...prev,
      [tno]: { ...prev[tno], [field]: value },
    }))
  }

  const handleSaveRow = async (teacher) => {
    const edits = rowEdits[teacher.tno] || {}
    const payload = {
      name: edits.name ?? teacher.name,
      title: edits.title ?? teacher.title,
      department: edits.department ?? teacher.department,
      email: edits.email ?? teacher.email,
      phone: edits.phone ?? teacher.phone,
    }
    try {
      await updateTeacher(teacher.tno, payload)
      setRowEdits((prev) => {
        const next = { ...prev }
        delete next[teacher.tno]
        return next
      })
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '更新教师失败')
    }
  }

  const handleDelete = async (tno) => {
    const confirmMessage =
      '根据参照完整性，删除教师将影响授课安排（不可置空），需要连同相关授课记录一起删除。是否继续执行？'
    if (!window.confirm(confirmMessage)) {
      return
    }
    try {
      await deleteTeacher(tno)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '删除教师失败')
    }
  }

  return (
    <>
      <CRow className="g-3 mb-4">
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">教师总数</p>
              <div className="display-6 fw-semibold">{meta?.stats?.total ?? '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">教授人数</p>
              <div className="display-6 fw-semibold">
                {meta?.stats?.title_distribution?.find((item) => item.label === 'Professor')?.value ?? 0}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">讲师人数</p>
              <div className="display-6 fw-semibold">
                {meta?.stats?.title_distribution?.find((item) => item.label === 'Lecturer')?.value ?? 0}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CRow className="g-4 mb-4">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>新增教师</strong>
            </CCardHeader>
            <CCardBody>
              <CForm className="row g-3" onSubmit={handleCreate}>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-tno">工号 *</CFormLabel>
                  <CFormInput id="create-tno" name="tno" value={createForm.tno} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-name">姓名 *</CFormLabel>
                  <CFormInput id="create-name" name="name" value={createForm.name} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-title">职称 *</CFormLabel>
                  <CFormSelect id="create-title" name="title" value={createForm.title} onChange={handleCreateChange} required>
                    <option value="">请选择职称</option>
                    {(meta?.titles || []).map((title) => (
                      <option key={title} value={title}>
                        {title}
                      </option>
                    ))}
                  </CFormSelect>
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
                  <CButton type="submit" color="primary" disabled={creating}>
                    {creating ? '提交中...' : '创建教师'}
                  </CButton>
                </CCol>
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>职称分布</strong>
            </CCardHeader>
            <CCardBody>
              {metaError && <CAlert color="danger">{metaError}</CAlert>}
              <CChartBar data={chartData} options={{ maintainAspectRatio: false }} style={{ height: '320px' }} />
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CCard>
        <CCardHeader className="d-flex flex-wrap justify-content-between align-items-end gap-3">
          <div>
            <h5 className="mb-0">教师列表</h5>
            <div className="text-body-secondary small">掌握师资结构与联系方式，支持快速检索</div>
          </div>
          <CButton color="secondary" variant="outline" onClick={resetFilters} disabled={loading}>
            重置
          </CButton>
        </CCardHeader>
        <CCardBody>
          <CForm className="row g-3 mb-4" onSubmit={applyFilters}>
            <CCol md={3}>
              <CFormLabel htmlFor="filter-teacher-name">姓名</CFormLabel>
              <CFormInput
                id="filter-teacher-name"
                name="name"
                value={formState.name}
                onChange={handleFilterChange}
                placeholder="例如：李老师"
              />
            </CCol>
            <CCol md={3}>
              <CFormLabel htmlFor="filter-teacher-email">邮箱</CFormLabel>
              <CFormInput
                id="filter-teacher-email"
                name="email"
                type="email"
                value={formState.email}
                onChange={handleFilterChange}
                placeholder="例如：teacher@example.com"
              />
            </CCol>
            <CCol md={3}>
              <CFormLabel htmlFor="filter-teacher-phone">电话</CFormLabel>
              <CFormInput
                id="filter-teacher-phone"
                name="phone"
                value={formState.phone}
                onChange={handleFilterChange}
                placeholder="例如：138****8888"
              />
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
            <CCol md={3}>
              <CFormLabel htmlFor="title">职称</CFormLabel>
              <CFormSelect id="title" name="title" value={formState.title} onChange={handleFilterChange}>
                <option value="">全部</option>
                {(meta?.titles || []).map((title) => (
                  <option key={title} value={title}>
                    {title}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={2} className="d-flex align-items-end">
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
            <div className="small text-body-secondary">共 {total} 名教师</div>
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
                  <CTableHeaderCell scope="col">工号</CTableHeaderCell>
                  <CTableHeaderCell scope="col">姓名</CTableHeaderCell>
                  <CTableHeaderCell scope="col">职称</CTableHeaderCell>
                  <CTableHeaderCell scope="col">院系</CTableHeaderCell>
                  <CTableHeaderCell scope="col">邮箱</CTableHeaderCell>
                  <CTableHeaderCell scope="col">电话</CTableHeaderCell>
                  <CTableHeaderCell scope="col" className="text-end">
                    操作
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {items.map((teacher) => {
                  const edits = rowEdits[teacher.tno] || {}
                  return (
                    <CTableRow key={teacher.tno}>
                      <CTableDataCell className="fw-semibold">{teacher.tno}</CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          value={edits.name ?? teacher.name}
                          onChange={(event) => handleRowChange(teacher.tno, 'name', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.title ?? teacher.title}
                          onChange={(event) => handleRowChange(teacher.tno, 'title', event.target.value)}
                        >
                          {(meta?.titles || []).map((title) => (
                            <option key={title} value={title}>
                              {title}
                            </option>
                          ))}
                        </CFormSelect>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormSelect
                          size="sm"
                          value={edits.department ?? teacher.department ?? ''}
                          onChange={(event) => handleRowChange(teacher.tno, 'department', event.target.value)}
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
                          type="email"
                          value={edits.email ?? teacher.email ?? ''}
                          onChange={(event) => handleRowChange(teacher.tno, 'email', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          value={edits.phone ?? teacher.phone ?? ''}
                          onChange={(event) => handleRowChange(teacher.tno, 'phone', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        <div className="d-flex justify-content-end gap-2">
                          <CButton size="sm" color="primary" variant="outline" onClick={() => handleSaveRow(teacher)}>
                            保存
                          </CButton>
                          <CButton size="sm" color="danger" variant="outline" onClick={() => handleDelete(teacher.tno)}>
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
              <div className="text-center py-5 text-body-secondary">暂无教师信息</div>
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

export default TeacherList
