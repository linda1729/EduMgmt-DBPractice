import { request } from './client'

export const listTeachings = ({ page = 1, perPage = 20, course, teacher, term, year } = {}) =>
  request('/api/v1/teachings/', {
    params: {
      page,
      per_page: perPage,
      course,
      teacher,
      term,
      year,
    },
  })

export const createTeaching = (payload) =>
  request('/api/v1/teachings/', { method: 'POST', data: payload })

export const updateTeaching = (teachId, payload) =>
  request(`/api/v1/teachings/${teachId}`, { method: 'PUT', data: payload })

export const deleteTeaching = (teachId) =>
  request(`/api/v1/teachings/${teachId}`, { method: 'DELETE' })

export const fetchTeachingMeta = () => request('/api/v1/teachings/meta')
