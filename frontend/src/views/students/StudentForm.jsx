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

import { createStudent, getStudent, updateStudent } from 'src/api/students'

const genderOptions = [
  { label: '男 (Male)', value: 'Male' },
  { label: '女 (Female)', value: 'Female' },
  { label: '其他 (Other)', value: 'Other' },
]

const defaultForm = {
  sno: '',
  name: '',
  gender: 'Male',
  enroll_year: '',
  department: '',
  birth_date: '',
  email: '',
  phone: '',
}

const StudentForm = () => {
  const { sno } = useParams()
  const isEdit = Boolean(sno)
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
        const data = await getStudent(sno)
        setForm({
          sno: data.sno,
          name: data.name,
          gender: data.gender,
          enroll_year: data.enroll_year,
          department: data.department || '',
          birth_date: data.birth_date || '',
          email: data.email || '',
          phone: data.phone || '',
        })
      } catch (err) {
        setError(err.message || '加载学生详情失败')
      } finally {
        setLoading(false)
      }
    }

    fetchDetail()
  }, [isEdit, sno])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (!form.sno || !form.name || !form.enroll_year) {
      setError('学号、姓名与入学年份为必填项')
      return
    }

    const payload = {
      sno: form.sno.trim(),
      name: form.name.trim(),
      gender: form.gender,
      enroll_year: Number(form.enroll_year),
      department: form.department || null,
      birth_date: form.birth_date || null,
      email: form.email || null,
      phone: form.phone || null,
    }

    if (Number.isNaN(payload.enroll_year)) {
      setError('入学年份需为数字')
      return
    }

    try {
      setSubmitting(true)
      if (isEdit) {
        await updateStudent(sno, payload)
      } else {
        await createStudent(payload)
      }
      navigate('/students')
    } catch (err) {
      setError(err.message || '提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <CCard>
      <CCardHeader>
        <h5 className="mb-0">{isEdit ? '编辑学生' : '新建学生'}</h5>
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
              <CFormLabel htmlFor="sno">学号</CFormLabel>
              <CFormInput
                id="sno"
                name="sno"
                value={form.sno}
                onChange={handleChange}
                disabled={isEdit}
                required
              />
            </CCol>
            <CCol md={6}>
              <CFormLabel htmlFor="name">姓名</CFormLabel>
              <CFormInput id="name" name="name" value={form.name} onChange={handleChange} required />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="gender">性别</CFormLabel>
              <CFormSelect id="gender" name="gender" value={form.gender} onChange={handleChange}>
                {genderOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="enroll_year">入学年份</CFormLabel>
              <CFormInput
                type="number"
                id="enroll_year"
                name="enroll_year"
                value={form.enroll_year}
                onChange={handleChange}
                required
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="department">院系编号</CFormLabel>
              <CFormInput
                id="department"
                name="department"
                value={form.department}
                onChange={handleChange}
                placeholder="选填"
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="birth_date">生日</CFormLabel>
              <CFormInput
                type="date"
                id="birth_date"
                name="birth_date"
                value={form.birth_date?.slice(0, 10) || ''}
                onChange={handleChange}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="email">邮箱</CFormLabel>
              <CFormInput id="email" name="email" value={form.email} onChange={handleChange} />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="phone">电话</CFormLabel>
              <CFormInput id="phone" name="phone" value={form.phone} onChange={handleChange} />
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

export default StudentForm
