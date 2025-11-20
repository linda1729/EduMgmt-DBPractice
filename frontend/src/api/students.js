import { request } from './client'

export const listStudents = ({ page = 1, perPage = 20, department, enrollYear, keyword } = {}) => {
  return request('/api/v1/students/', {
    params: {
      page,
      per_page: perPage,
      department,
      enroll_year: enrollYear,
      q: keyword,
    },
  })
}

export const getStudent = (sno) => request(`/api/v1/students/${sno}`)

export const createStudent = (payload) => request('/api/v1/students/', { method: 'POST', data: payload })

export const updateStudent = (sno, payload) =>
  request(`/api/v1/students/${sno}`, { method: 'PUT', data: payload })

export const deleteStudent = (sno) => request(`/api/v1/students/${sno}`, { method: 'DELETE' })

export const fetchStudentMeta = () => request('/api/v1/students/meta')
