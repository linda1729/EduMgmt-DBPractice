import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
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
  CFormSwitch,
  CSpinner,
} from '@coreui/react'

import { createCourse, getCourse, updateCourse } from 'src/api/courses'

const defaultForm = {
  cno: '',
  name: '',
  credits: 1,
  hours: 16,
  department: '',
  prerequisite: '',
  is_active: true,
}

const CourseForm = () => {
  const { cno } = useParams()
  const isEdit = Boolean(cno)
  const [form, setForm] = useState(defaultForm)
  const [loading, setLoading] = useState(isEdit)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!isEdit) {
      return
    }
    const fetchDetail = async () => {
      setLoading(true)
      setError('')
      try {
        const data = await getCourse(cno)
        setForm({
          cno: data.cno,
          name: data.name,
          credits: data.credits,
          hours: data.hours,
          department: data.department || '',
          prerequisite: data.prerequisite || '',
          is_active: Boolean(data.is_active),
        })
      } catch (err) {
        setError(err.message || '加载课程失败')
      } finally {
        setLoading(false)
      }
    }

    fetchDetail()
  }, [cno, isEdit])

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (!form.cno || !form.name) {
      setError('课程号与名称必填')
      return
    }

    const credits = Number(form.credits)
    const hours = Number(form.hours)
    if (Number.isNaN(credits) || Number.isNaN(hours)) {
      setError('学分与学时需为数字')
      return
    }

    const payload = {
      cno: form.cno.trim(),
      name: form.name.trim(),
      credits,
      hours,
      department: form.department || null,
      prerequisite: form.prerequisite || null,
      is_active: Boolean(form.is_active),
    }

    try {
      setSubmitting(true)
      if (isEdit) {
        await updateCourse(cno, payload)
      } else {
        await createCourse(payload)
      }
      navigate('/courses')
    } catch (err) {
      setError(err.message || '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <CCard>
      <CCardHeader>
        <h5 className="mb-0">{isEdit ? '编辑课程' : '新建课程'}</h5>
      </CCardHeader>
      <CCardBody>
        {loading ? (
          <div className="text-center py-5">
            <CSpinner color="primary" />
          </div>
        ) : (
          <CForm onSubmit={handleSubmit} className="row g-4">
            {error && (
              <CCol xs={12}>
                <CAlert color="danger">{error}</CAlert>
              </CCol>
            )}
            <CCol md={6}>
              <CFormLabel htmlFor="cno">课程号</CFormLabel>
              <CFormInput id="cno" name="cno" value={form.cno} onChange={handleChange} disabled={isEdit} required />
            </CCol>
            <CCol md={6}>
              <CFormLabel htmlFor="name">课程名称</CFormLabel>
              <CFormInput id="name" name="name" value={form.name} onChange={handleChange} required />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="credits">学分</CFormLabel>
              <CFormInput
                type="number"
                min={1}
                id="credits"
                name="credits"
                value={form.credits}
                onChange={handleChange}
                required
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="hours">学时</CFormLabel>
              <CFormInput
                type="number"
                min={1}
                id="hours"
                name="hours"
                value={form.hours}
                onChange={handleChange}
                required
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="department">院系编号</CFormLabel>
              <CFormInput id="department" name="department" value={form.department} onChange={handleChange} />
            </CCol>
            <CCol md={6}>
              <CFormLabel htmlFor="prerequisite">先修课程号</CFormLabel>
              <CFormInput
                id="prerequisite"
                name="prerequisite"
                value={form.prerequisite}
                onChange={handleChange}
                placeholder="选填"
              />
            </CCol>
            <CCol md={6} className="d-flex align-items-end">
              <CFormSwitch
                id="is_active"
                name="is_active"
                label="课程可选"
                checked={form.is_active}
                onChange={handleChange}
              />
            </CCol>
            <CCol xs={12} className="d-flex gap-3">
              <CButton type="submit" color="primary" disabled={submitting}>
                {submitting ? '保存中…' : '保存'}
              </CButton>
              <CButton type="button" variant="ghost" color="secondary" onClick={() => navigate(-1)}>
                取消
              </CButton>
            </CCol>
          </CForm>
        )}
      </CCardBody>
    </CCard>
  )
}

export default CourseForm
