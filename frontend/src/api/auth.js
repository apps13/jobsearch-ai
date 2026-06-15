import { get, post } from './client'

export function getCurrentUser() {
  return get('/api/auth/me')
}

export function logout() {
  return post('/api/auth/logout')
}
