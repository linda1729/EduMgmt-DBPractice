import { request } from './client'

export const listEnrollments = ({
  page = 1,
  perPage = 20,
  student,
  course,
  status,
  year,
  term,
} = {}) => {
  return request('/api/v1/enrollments/', {
    params: {
      page,
      per_page: perPage,
      student,
      course,
      status,
      year,
      term,
    },
  })
}

export const getEnrollment = (studentId, courseId) =>
  request(`/api/v1/enrollments/${studentId}/${courseId}`)

export const createEnrollment = (payload) =>
  request('/api/v1/enrollments/', { method: 'POST', data: payload })

export const updateEnrollment = (studentId, courseId, payload) =>
  request(`/api/v1/enrollments/${studentId}/${courseId}`, { method: 'PUT', data: payload })

export const deleteEnrollment = (studentId, courseId) =>
  request(`/api/v1/enrollments/${studentId}/${courseId}`, { method: 'DELETE' })

export const fetchEnrollmentMeta = () => request('/api/v1/enrollments/meta')
