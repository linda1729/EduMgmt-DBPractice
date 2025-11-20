import { request } from './client'

export const listCourses = ({
  page = 1,
  perPage = 20,
  department,
  courseId,
  name,
  includeInactive = false,
} = {}) => {
  return request('/api/v1/courses/', {
    params: {
      page,
      per_page: perPage,
      department,
      cno: courseId,
      name,
      include_inactive: includeInactive ? 'true' : undefined,
    },
  })
}

export const getCourse = (cno) => request(`/api/v1/courses/${cno}`)

export const createCourse = (payload) => request('/api/v1/courses/', { method: 'POST', data: payload })

export const updateCourse = (cno, payload) =>
  request(`/api/v1/courses/${cno}`, { method: 'PUT', data: payload })

export const deleteCourse = (cno) => request(`/api/v1/courses/${cno}`, { method: 'DELETE' })

export const fetchCourseMeta = () => request('/api/v1/courses/meta')
