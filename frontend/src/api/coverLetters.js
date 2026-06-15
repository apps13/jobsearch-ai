import { del, get, post } from './client'

export function generateCoverLetter(payload) {
  return post('/api/cover-letter', payload)
}

export function getCoverLetterHistory() {
  return get('/api/cover-letter')
}

export function deleteCoverLetter(id) {
  return del('/api/cover-letter/' + id)
}
