import React, { useEffect, useMemo, useState } from 'react'
import {
  CAlert,
  CBadge,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilBuilding, cilBook, cilPeople, cilSpreadsheet } from '@coreui/icons'
import { CChartBar, CChartDoughnut } from '@coreui/react-chartjs'

import { fetchDashboardSummary } from 'src/api/dashboard'

const statCards = [
  { key: 'students', label: '学生总数', icon: cilPeople },
  { key: 'courses', label: '课程数量', icon: cilBook },
  { key: 'teachers', label: '授课教师', icon: cilPeople },
  { key: 'classrooms', label: '教室数量', icon: cilBuilding },
  { key: 'enrollments', label: '选课记录', icon: cilSpreadsheet },
]

const statusMeta = {
  enrolled: { color: 'info', label: '在读' },
  completed: { color: 'success', label: '已结课' },
  dropped: { color: 'danger', label: '退课' },
}

const heatmapColumns = [
  { key: 'create', label: '增' },
  { key: 'read', label: '查' },
  { key: 'update', label: '改' },
  { key: 'delete', label: '删' },
]

const Dashboard = () => {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const data = await fetchDashboardSummary()
        setSummary(data)
      } catch (err) {
        setError(err.message || '加载仪表盘数据失败')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  const courseChartData = useMemo(() => {
    const labels = summary?.top_courses?.labels ?? []
    const values = summary?.top_courses?.values ?? []
    if (!labels.length) {
      return {
        labels: ['暂无数据'],
        datasets: [{ label: '选课人数', data: [0], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels,
      datasets: [
        {
          label: '选课人数',
          data: values,
          backgroundColor: labels.map((_, idx) => `hsla(${(idx * 70) % 360}, 70%, 60%, 0.85)`),
          borderRadius: 8,
        },
      ],
    }
  }, [summary])

  const statusChartData = useMemo(() => {
    const labels = summary?.status_chart?.labels ?? []
    const values = summary?.status_chart?.values ?? []
    if (!labels.length) {
      return {
        labels: ['暂无数据'],
        datasets: [{ data: [1], backgroundColor: ['#e5e7eb'] }],
      }
    }
    return {
      labels: labels.map((label) => statusMeta[label]?.label || label),
      datasets: [
        {
          data: values,
          backgroundColor: ['#0ea5e9', '#10b981', '#f97316', '#f43f5e'],
        },
      ],
    }
  }, [summary])

  const statusEntries = useMemo(() => {
    const labels = summary?.status_chart?.labels ?? []
    const values = summary?.status_chart?.values ?? []
    return labels.map((label, idx) => ({
      key: label,
      label: statusMeta[label]?.label || label,
      color: statusMeta[label]?.color || 'secondary',
      count: values[idx] ?? 0,
    }))
  }, [summary])

  const crudHeatmap = summary?.crud_heatmap ?? []
  const heatmapMax = useMemo(() => {
    if (crudHeatmap.length === 0) return 0
    return crudHeatmap.reduce((max, row) => {
      const rowMax = Math.max(
        ...heatmapColumns.map((col) => Number(row.metrics?.[col.key] ?? 0)),
      )
      return Math.max(max, rowMax)
    }, 0)
  }, [crudHeatmap])

  const renderHeatmapCellStyle = (value) => {
    if (!heatmapMax) {
      return { backgroundColor: 'rgba(148, 163, 184, 0.15)' }
    }
    const intensity = value / heatmapMax
    const lightness = 88 - intensity * 45
    const alpha = 0.25 + intensity * 0.55
    const bg = `hsla(${200 - intensity * 60}, 80%, ${lightness}%, ${alpha})`
    const textColor = intensity > 0.55 ? '#fff' : '#0f172a'
    return {
      backgroundColor: bg,
      color: textColor,
      fontWeight: intensity > 0.5 ? 600 : 500,
    }
  }

  const formatDate = (value) => {
    if (!value) return '-'
    try {
      return new Date(value).toLocaleString()
    } catch (err) {
      return value
    }
  }

  if (loading) {
    return (
      <div className="text-center py-5">
        <CSpinner color="primary" />
      </div>
    )
  }

  if (error) {
    return <CAlert color="danger">{error}</CAlert>
  }

  if (!summary) {
    return <CAlert color="warning">暂无仪表盘数据</CAlert>
  }

  const totals = summary?.totals ?? {}
  const activeTerms = summary?.active_terms ?? []
  const topCourses = summary?.top_courses?.rows ?? []
  const recentEnrollments = summary?.recent_enrollments ?? []

  return (
    <>
      <CRow className="g-3 mb-4">
        {statCards.map((card) => (
          <CCol sm={6} xl={12 / statCards.length} key={card.key}>
            <CCard className="h-100">
              <CCardBody className="d-flex align-items-center justify-content-between">
                <div>
                  <div className="text-body-secondary text-uppercase small mb-1">{card.label}</div>
                  <div className="fs-3 fw-semibold">{totals[card.key] ?? '-'}</div>
                </div>
                <div className="text-primary bg-primary-subtle rounded-circle p-3">
                  <CIcon icon={card.icon} size="xl" />
                </div>
              </CCardBody>
            </CCard>
          </CCol>
        ))}
      </CRow>

      <CRow className="g-3 mb-4">
        <CCol>
          <CCard className="h-100">
            <CCardHeader>
              <strong>各表增删查改热力图</strong>
              <div className="text-body-secondary small">
                统计近 30 天内的增/查/改行为强度与依赖关系（删）
              </div>
            </CCardHeader>
            <CCardBody>
              {crudHeatmap.length === 0 ? (
                <div className="text-body-secondary">暂无增删查改统计数据</div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-sm text-center align-middle">
                    <thead>
                      <tr>
                        <th scope="col" className="text-start">
                          数据表
                        </th>
                        {heatmapColumns.map((col) => (
                          <th key={col.key} scope="col">
                            {col.label}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {crudHeatmap.map((row) => (
                        <tr key={row.table}>
                          <th scope="row" className="text-start">
                            {row.table}
                          </th>
                          {heatmapColumns.map((col) => {
                            const value = Number(row.metrics?.[col.key] ?? 0)
                            return (
                              <td key={col.key}>
                                <div
                                  className="py-2 rounded-2"
                                  style={renderHeatmapCellStyle(value)}
                                >
                                  {value.toLocaleString()}
                                </div>
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CRow className="g-3 mb-4">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>热门课程走势</strong>
              <div className="text-body-secondary small">选课人数 Top5 柱状图</div>
            </CCardHeader>
            <CCardBody>
              <CChartBar data={courseChartData} options={{ maintainAspectRatio: false }} style={{ height: '320px' }} />
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>选课状态分布</strong>
              <div className="text-body-secondary small">全量选课状态占比</div>
            </CCardHeader>
            <CCardBody>
              <CChartDoughnut
                data={statusChartData}
                options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }}
                style={{ height: '320px' }}
              />
              <div className="mt-3">
                {statusEntries.length === 0 && <div className="text-body-secondary">暂无状态数据</div>}
                {statusEntries.map((entry) => (
                  <div key={entry.key} className="d-flex justify-content-between align-items-center mb-2">
                    <div>
                      <CBadge color={entry.color} className="me-2">
                        {entry.label}
                      </CBadge>
                      <span className="text-body-secondary">选课状态</span>
                    </div>
                    <strong>{entry.count}</strong>
                  </div>
                ))}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CCard className="mb-4">
        <CCardHeader>
          <strong>核心数据摘要</strong>
        </CCardHeader>
        <CCardBody className="p-0">
          <div className="table-responsive">
            <CTable align="middle" className="mb-0">
              <CTableHead color="light">
                <CTableRow>
                  <CTableHeaderCell scope="col">指标</CTableHeaderCell>
                  <CTableHeaderCell scope="col">数值</CTableHeaderCell>
                  <CTableHeaderCell scope="col">备注</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                <CTableRow>
                  <CTableDataCell>学生总数</CTableDataCell>
                  <CTableDataCell className="fw-semibold">{totals.students ?? '-'}</CTableDataCell>
                  <CTableDataCell>包含所有在籍学生</CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableDataCell>课程数量</CTableDataCell>
                  <CTableDataCell className="fw-semibold">{totals.courses ?? '-'}</CTableDataCell>
                  <CTableDataCell>当前开放课程</CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableDataCell>授课教师</CTableDataCell>
                  <CTableDataCell className="fw-semibold">{totals.teachers ?? '-'}</CTableDataCell>
                  <CTableDataCell>专任 / 兼职教师</CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableDataCell>教室数量</CTableDataCell>
                  <CTableDataCell className="fw-semibold">{totals.classrooms ?? '-'}</CTableDataCell>
                  <CTableDataCell>可用授课场地</CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableDataCell>活跃学期</CTableDataCell>
                  <CTableDataCell className="fw-semibold">{activeTerms.length}</CTableDataCell>
                  <CTableDataCell>{activeTerms.join('、') || '暂无数据'}</CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableDataCell>选课记录</CTableDataCell>
                  <CTableDataCell className="fw-semibold">{totals.enrollments ?? '-'}</CTableDataCell>
                  <CTableDataCell>SC 表累计数据</CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>
        </CCardBody>
      </CCard>

      <CRow className="g-3">
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>选课热门课程</strong>
              <div className="text-body-secondary small">Top5 课程及人数</div>
            </CCardHeader>
            <CCardBody className="p-0">
              <div className="table-responsive">
                <CTable hover align="middle" className="mb-0">
                  <CTableHead color="light">
                    <CTableRow>
                      <CTableHeaderCell scope="col">课程号</CTableHeaderCell>
                      <CTableHeaderCell scope="col">课程名称</CTableHeaderCell>
                      <CTableHeaderCell scope="col" className="text-end">
                        选课人数
                      </CTableHeaderCell>
                    </CTableRow>
                  </CTableHead>
                  <CTableBody>
                    {topCourses.map((item) => (
                      <CTableRow key={item.course_id}>
                        <CTableDataCell className="fw-semibold">{item.course_id}</CTableDataCell>
                        <CTableDataCell>{item.course_name}</CTableDataCell>
                        <CTableDataCell className="text-end">
                          <CBadge color="primary" className="px-3">
                            {item.enrolled_count}
                          </CBadge>
                        </CTableDataCell>
                      </CTableRow>
                    ))}
                  </CTableBody>
                </CTable>
              </div>
              {topCourses.length === 0 && (
                <div className="text-center py-4 text-body-secondary">暂无热门课程数据</div>
              )}
            </CCardBody>
          </CCard>
        </CCol>
        <CCol lg={6}>
          <CCard className="h-100">
            <CCardHeader>
              <strong>最新选课记录</strong>
              <div className="text-body-secondary small">实时掌握学生动向</div>
            </CCardHeader>
            <CCardBody>
              <div className="table-responsive">
                <CTable hover align="middle">
                  <CTableHead>
                    <CTableRow>
                      <CTableHeaderCell scope="col">学生</CTableHeaderCell>
                      <CTableHeaderCell scope="col">课程</CTableHeaderCell>
                      <CTableHeaderCell scope="col">状态</CTableHeaderCell>
                      <CTableHeaderCell scope="col">成绩</CTableHeaderCell>
                      <CTableHeaderCell scope="col">选课时间</CTableHeaderCell>
                    </CTableRow>
                  </CTableHead>
                  <CTableBody>
                    {recentEnrollments.map((item) => (
                      <CTableRow key={`${item.student_id}-${item.course_id}-${item.enroll_date}`}>
                        <CTableDataCell>
                          <div className="fw-semibold">{item.student_name}</div>
                          <div className="text-body-secondary small">{item.student_id}</div>
                        </CTableDataCell>
                        <CTableDataCell>
                          <div className="fw-semibold">{item.course_name}</div>
                          <div className="text-body-secondary small">{item.course_id}</div>
                        </CTableDataCell>
                        <CTableDataCell>
                          <CBadge color={(statusMeta[item.status] || {}).color || 'secondary'}>
                            {statusMeta[item.status]?.label || item.status}
                          </CBadge>
                        </CTableDataCell>
                        <CTableDataCell>{item.grade ?? '-'}</CTableDataCell>
                        <CTableDataCell>{formatDate(item.enroll_date)}</CTableDataCell>
                      </CTableRow>
                    ))}
                  </CTableBody>
                </CTable>
              </div>
              {recentEnrollments.length === 0 && (
                <div className="text-center py-4 text-body-secondary">暂无选课记录</div>
              )}
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </>
  )
}

export default Dashboard
