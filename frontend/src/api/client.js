export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, { ...options, credentials: 'include' })

  const text = await res.text()
  const data = text ? JSON.parse(text) : null

  if (!res.ok) {
    const detail = data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : detail
          ? JSON.stringify(detail)
          : res.statusText || 'Request failed'
    throw new Error(message)
  }

  return data
}

export function get(path) {
  return request(path)
}

export function post(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function postForm(path, formData) {
  return request(path, {
    method: 'POST',
    body: formData,
  })
}

export function del(path) {
  return request(path, { method: 'DELETE' })
}
