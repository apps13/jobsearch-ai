import { get, patch, post } from './client'

export function listUsers(status) {
  const query = status ? `?status=${status}` : ''
  return get(`/api/admin/users${query}`)
}

export function unblockUser(id) {
  return post(`/api/admin/users/${id}/approve`)
}

export function blockUser(id) {
  return post(`/api/admin/users/${id}/reject`)
}

export function updateGenerationLimit(id, limit) {
  return patch(`/api/admin/users/${id}/limit`, { generation_limit: limit })
}
