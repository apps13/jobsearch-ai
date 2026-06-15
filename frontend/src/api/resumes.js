import { get, postForm } from './client'

export function getResumes() {
  return get('/api/resumes')
}

export function uploadResume({ label, file }) {
  const formData = new FormData()
  formData.append('label', label)
  formData.append('file', file)
  return postForm('/api/resumes/upload', formData)
}
