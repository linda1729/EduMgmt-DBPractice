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
  CFormSelect,
  CSpinner,
} from '@coreui/react'

import { createEnrollment, getEnrollment, updateEnrollment } from 'src/api/enrollments'
import { ACADEMIC_YEAR_MIN, GRADE_MAX, GRADE_MIN } from 'src/constants/integrity'

const statusOptions = [
  { label: '在读 (enrolled)', value: 'enrolled' },
  { label: '已结课 (completed)', value: 'completed' },
  { label: '退课 (dropped)', value: 'dropped' },
]

const defaultForm = {
  student_id: '',
  course_id: '',
  year: '',
  term: '',
  status: 'enrolled',
  grade: '',
}

const EnrollmentForm = () => {
  const { studentId, courseId } = useParams()
  const isEdit = Boolean(studentId && courseId)
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
        const data = await getEnrollment(studentId, courseId)
        setForm({
          student_id: data.student_id,
          course_id: data.course_id,
          year: data.year || '',
          term: data.term || '',
          status: data.status,
          grade: data.grade ?? '',
        })
      } catch (err) {
        setError(err.message || '加载选课记录失败')
      } finally {
        setLoading(false)
      }
    }

    fetchDetail()
  }, [courseId, isEdit, studentId])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (!form.student_id || !form.course_id || !form.year || !form.term) {
      setError('请完整填写学号、课程号、学年与学期')
      return
    }

    const yearValue = Number(form.year)
    if (!Number.isInteger(yearValue) || yearValue < ACADEMIC_YEAR_MIN) {
      setError(`学年需为不小于 ${ACADEMIC_YEAR_MIN} 的整数`)
      return
    }
    let gradeValue = null
    if (form.grade !== '') {
      const parsedGrade = Number(form.grade)
      if (Number.isNaN(parsedGrade) || parsedGrade < GRADE_MIN || parsedGrade > GRADE_MAX) {
        setError(`成绩需介于 ${GRADE_MIN}-${GRADE_MAX}`)
        return
      }
      gradeValue = parsedGrade
    }

    const payload = {
      student_id: form.student_id.trim(),
      course_id: form.course_id.trim(),
      year: yearValue,
      term: form.term.trim(),
      status: form.status,
      grade: gradeValue,
    }

    try {
      setSubmitting(true)
      if (isEdit) {
        await updateEnrollment(studentId, courseId, payload)
      } else {
        await createEnrollment(payload)
      }
      navigate('/enrollments')
    } catch (err) {
      setError(err.message || '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <CCard>
      <CCardHeader>
        <h5 className="mb-0">{isEdit ? '编辑选课记录' : '新增选课记录'}</h5>
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
              <CFormLabel htmlFor="student_id">学号</CFormLabel>
              <CFormInput
                id="student_id"
                name="student_id"
                value={form.student_id}
                onChange={handleChange}
                disabled={isEdit}
                required
              />
            </CCol>
            <CCol md={6}>
              <CFormLabel htmlFor="course_id">课程号</CFormLabel>
              <CFormInput
                id="course_id"
                name="course_id"
                value={form.course_id}
                onChange={handleChange}
                disabled={isEdit}
                required
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="year">学年</CFormLabel>
              <CFormInput
                type="number"
                id="year"
                name="year"
                min={ACADEMIC_YEAR_MIN}
                value={form.year}
                onChange={handleChange}
                required
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="term">学期</CFormLabel>
              <CFormInput id="term" name="term" value={form.term} onChange={handleChange} required />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="status">状态</CFormLabel>
              <CFormSelect id="status" name="status" value={form.status} onChange={handleChange}>
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={6}>
              <CFormLabel htmlFor="grade">成绩（0-100）</CFormLabel>
              <CFormInput
                type="number"
                id="grade"
                name="grade"
                min={GRADE_MIN}
                max={GRADE_MAX}
                value={form.grade}
                onChange={handleChange}
                placeholder="选填"
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

export default EnrollmentForm
