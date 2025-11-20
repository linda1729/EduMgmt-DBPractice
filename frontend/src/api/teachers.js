import { request } from './client'

export const listTeachers = ({ page = 1, perPage = 20, department, title, keyword } = {}) =>
  request('/api/v1/teachers/', {
    params: {
      page,
      per_page: perPage,
      department,
      title,
      q: keyword,
    },
  })

export const createTeacher = (payload) => request('/api/v1/teachers/', { method: 'POST', data: payload })

export const updateTeacher = (tno, payload) =>
  request(`/api/v1/teachers/${tno}`, { method: 'PUT', data: payload })

export const deleteTeacher = (tno) => request(`/api/v1/teachers/${tno}`, { method: 'DELETE' })

export const fetchTeacherMeta = () => request('/api/v1/teachers/meta')
