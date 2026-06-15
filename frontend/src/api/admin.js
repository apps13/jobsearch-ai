import { get, post } from './client'

export function listUsers(status) {
  const query = status ? `?status=${status}` : ''
  return get(`/api/admin/users${query}`)
}

export function approveUser(id) {
  return post(`/api/admin/users/${id}/approve`)
}

export function rejectUser(id) {
  return post(`/api/admin/users/${id}/reject`)
}
