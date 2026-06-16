import { useEffect, useState } from 'react'
import { deleteCoverLetter, getCoverLetterHistory } from '../api/coverLetters'
import { CoverLetterText, FitAnalysis } from './ResultView'

function HistoryItem({ entry, onDeleted }) {
  const [expanded, setExpanded] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)

  const handleDelete = async () => {
    if (!confirm('Delete this entry from your history?')) return
    setDeleting(true)
    setError(null)
    try {
      await deleteCoverLetter(entry.id)
      onDeleted(entry.id)
    } catch (err) {
      setError(err.message)
      setDeleting(false)
    }
  }

  const matchScore = entry.fit_analysis?.match_score
  const hasCoverLetter = Boolean(entry.cover_letter)
  const hasWtc = Boolean(entry.why_this_company)

  return (
    <li className="history-item">
      <button type="button" className="history-summary" onClick={() => setExpanded((v) => !v)}>
        <span>Role #{entry.role_id}</span>
        {matchScore != null && (
          <span className="match-score">Match score: {matchScore}%</span>
        )}
        <span className="muted">{new Date(entry.created_at).toLocaleString()}</span>
        <span>{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div className="history-detail">
          {hasCoverLetter && <CoverLetterText coverLetter={entry.cover_letter} />}
          {hasWtc && (
            <div className="why-this-company">
              <h4>Why This Company</h4>
              <p>{entry.why_this_company}</p>
            </div>
          )}
          {entry.fit_analysis && <FitAnalysis fitAnalysis={entry.fit_analysis} />}
          {error && <p className="error">{error}</p>}
          <div className="history-delete">
            <button type="button" className="btn-delete" onClick={handleDelete} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      )}
    </li>
  )
}

export default function HistoryList({ refreshKey }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setHistory(await getCoverLetterHistory())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [refreshKey])

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>History</h2>
        <button type="button" onClick={load} disabled={loading}>
          Refresh
        </button>
      </div>

      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="muted">Loading...</p>
      ) : history.length === 0 ? (
        <p className="muted">No generations yet.</p>
      ) : (
        <ul className="history-list">
          {history.map((entry) => (
            <HistoryItem
              key={entry.id}
              entry={entry}
              onDeleted={(id) => setHistory((h) => h.filter((item) => item.id !== id))}
            />
          ))}
        </ul>
      )}
    </div>
  )
}
