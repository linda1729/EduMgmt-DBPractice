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
  createClassroom,
  deleteClassroom,
  fetchClassroomMeta,
  listClassrooms,
  updateClassroom,
} from 'src/api/classrooms'
import PaginationControls from 'src/components/PaginationControls'

const pageSizeOptions = [10, 20, 50]

const defaultCreateState = {
  room_id: '',
  building: '',
  room_no: '',
  capacity: '',
}

const ClassroomList = () => {
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState('')
  const [formState, setFormState] = useState({ building: '', q: '' })
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
        const data = await fetchClassroomMeta()
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
        const response = await listClassrooms({
          page,
          perPage,
          building: filters.building || undefined,
          keyword: filters.q || undefined,
        })
        setItems(response.items || [])
        setTotal(response.total || 0)
      } catch (err) {
        setError(err.message || '加载教室失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [filters, page, perPage, refreshKey])

  const buildingOptions = useMemo(() => {
    const distribution = meta?.stats?.building_distribution ?? []
    if (!distribution.length) {
      return []
    }
    return distribution.map((item) => item.label || '未分配')
  }, [meta])

  const chartData = useMemo(() => {
    const distribution = meta?.stats?.building_distribution ?? []
    if (!distribution.length) {
      return {
        labels: ['暂无数据'],
        datasets: [{ label: '教室数量', data: [0], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels: distribution.map((item) => item.label || '未分配'),
      datasets: [
        {
          label: '教室数量',
          data: distribution.map((item) => item.value),
          backgroundColor: distribution.map((_, idx) => `hsla(${(idx * 75) % 360}, 65%, 60%, 0.85)`),
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
    const next = { building: '', q: '' }
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
      if (!createForm.room_id || !createForm.building || !createForm.room_no || !createForm.capacity) {
        throw new Error('请填写教室编号、楼栋、房间号与容量')
      }
      await createClassroom({
        room_id: createForm.room_id.trim(),
        building: createForm.building.trim(),
        room_no: createForm.room_no.trim(),
        capacity: Number(createForm.capacity),
      })
      setCreateForm(defaultCreateState)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '创建教室失败')
    } finally {
      setCreating(false)
    }
  }

  const handleRowChange = (roomId, field, value) => {
    setRowEdits((prev) => ({
      ...prev,
      [roomId]: { ...prev[roomId], [field]: value },
    }))
  }

  const handleSaveRow = async (classroom) => {
    const edits = rowEdits[classroom.room_id] || {}
    const payload = {}
    if (edits.building !== undefined) payload.building = edits.building
    if (edits.room_no !== undefined) payload.room_no = edits.room_no
    if (edits.capacity !== undefined) payload.capacity = Number(edits.capacity)
    try {
      await updateClassroom(classroom.room_id, payload)
      setRowEdits((prev) => {
        const next = { ...prev }
        delete next[classroom.room_id]
        return next
      })
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '更新教室失败')
    }
  }

  const handleDelete = async (roomId) => {
    if (!window.confirm(`确认删除教室 ${roomId} 吗？`)) {
      return
    }
    try {
      await deleteClassroom(roomId)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err.message || '删除教室失败')
    }
  }

  if (loading && !items.length && !meta) {
    return (
      <div className="text-center py-5">
        <CSpinner color="primary" />
      </div>
    )
  }

  return (
    <>
      <CRow className="g-3 mb-4">
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">教室总数</p>
              <div className="display-6 fw-semibold">{meta?.stats?.total ?? '-'}</div>
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
        <CCol md={4}>
          <CCard className="h-100">
            <CCardBody className="text-center">
              <p className="text-uppercase text-body-secondary small mb-1">楼栋数量</p>
              <div className="display-6 fw-semibold">{buildingOptions.length || '-'}</div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CRow className="g-4 mb-4">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>新增教室</strong>
            </CCardHeader>
            <CCardBody>
              <CForm className="row g-3" onSubmit={handleCreate}>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-room-id">教室编号 *</CFormLabel>
                  <CFormInput id="create-room-id" name="room_id" value={createForm.room_id} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-building">楼栋 *</CFormLabel>
                  <CFormInput id="create-building" name="building" value={createForm.building} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-room-no">房间号 *</CFormLabel>
                  <CFormInput id="create-room-no" name="room_no" value={createForm.room_no} onChange={handleCreateChange} required />
                </CCol>
                <CCol sm={6}>
                  <CFormLabel htmlFor="create-capacity">容量 *</CFormLabel>
                  <CFormInput
                    id="create-capacity"
                    name="capacity"
                    type="number"
                    value={createForm.capacity}
                    onChange={handleCreateChange}
                    required
                  />
                </CCol>
                <CCol xs={12} className="text-end">
                  <CButton type="submit" color="primary" disabled={creating}>
                    {creating ? '提交中...' : '创建教室'}
                  </CButton>
                </CCol>
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>楼栋分布</strong>
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
            <h5 className="mb-0">教室列表</h5>
            <div className="text-body-secondary small">维护教学场地基础信息，支持模糊检索</div>
          </div>
          <CButton color="secondary" variant="outline" onClick={resetFilters} disabled={loading}>
            重置
          </CButton>
        </CCardHeader>
        <CCardBody>
          <CForm className="row g-3 mb-4" onSubmit={applyFilters}>
            <CCol md={4}>
              <CFormLabel htmlFor="building">楼栋</CFormLabel>
              <CFormSelect id="building" name="building" value={formState.building} onChange={handleFilterChange}>
                <option value="">全部楼栋</option>
                {buildingOptions.map((label) => (
                  <option key={label} value={label}>
                    {label}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={7}>
              <CFormLabel htmlFor="q">关键字（编号/房间号）</CFormLabel>
              <CFormInput id="q" name="q" value={formState.q} onChange={handleFilterChange} placeholder="例如：A1 或 101" />
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
            <div className="small text-body-secondary">共 {total} 间教室</div>
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
                  <CTableHeaderCell scope="col">教室编号</CTableHeaderCell>
                  <CTableHeaderCell scope="col">楼栋</CTableHeaderCell>
                  <CTableHeaderCell scope="col">房间号</CTableHeaderCell>
                  <CTableHeaderCell scope="col">容量</CTableHeaderCell>
                  <CTableHeaderCell scope="col" className="text-end">
                    操作
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {items.map((room) => {
                  const edits = rowEdits[room.room_id] || {}
                  return (
                    <CTableRow key={room.room_id}>
                      <CTableDataCell className="fw-semibold">{room.room_id}</CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          value={edits.building ?? room.building}
                          onChange={(event) => handleRowChange(room.room_id, 'building', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          value={edits.room_no ?? room.room_no}
                          onChange={(event) => handleRowChange(room.room_id, 'room_no', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CFormInput
                          size="sm"
                          type="number"
                          value={edits.capacity ?? room.capacity}
                          onChange={(event) => handleRowChange(room.room_id, 'capacity', event.target.value)}
                        />
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        <div className="d-flex justify-content-end gap-2">
                          <CButton size="sm" color="primary" variant="outline" onClick={() => handleSaveRow(room)}>
                            保存
                          </CButton>
                          <CButton size="sm" color="danger" variant="outline" onClick={() => handleDelete(room.room_id)}>
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
              <div className="text-center py-5 text-body-secondary">暂无教室数据</div>
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

export default ClassroomList
