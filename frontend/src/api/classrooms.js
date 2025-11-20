import { request } from './client'

export const listClassrooms = ({
  page = 1,
  perPage = 20,
  building,
  roomId,
  roomNo,
  keyword,
} = {}) =>
  request('/api/v1/classrooms/', {
    params: {
      page,
      per_page: perPage,
      building,
      room_id: roomId,
      room_no: roomNo,
      q: keyword,
    },
  })

export const createClassroom = (payload) =>
  request('/api/v1/classrooms/', { method: 'POST', data: payload })

export const updateClassroom = (roomId, payload) =>
  request(`/api/v1/classrooms/${roomId}`, { method: 'PUT', data: payload })

export const deleteClassroom = (roomId) =>
  request(`/api/v1/classrooms/${roomId}`, { method: 'DELETE' })

export const fetchClassroomMeta = () => request('/api/v1/classrooms/meta')
