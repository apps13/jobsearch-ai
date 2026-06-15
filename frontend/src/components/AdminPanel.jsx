import { useEffect, useState } from 'react'
import { approveUser, listUsers, rejectUser } from '../api/admin'

const FILTERS = [
  { id: '', label: 'All' },
  { id: 'pending', label: 'Pending' },
  { id: 'approved', label: 'Approved' },
  { id: 'rejected', label: 'Rejected' },
]

export default function AdminPanel() {
  const [filter, setFilter] = useState('pending')
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setUsers(await listUsers(filter || undefined))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  const handleApprove = async (id) => {
    try {
      await approveUser(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleReject = async (id) => {
    try {
      await rejectUser(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Admin</h2>
        <button type="button" onClick={load} disabled={loading}>
          Refresh
        </button>
      </div>

      <div className="resume-mode-toggle">
        {FILTERS.map((f) => (
          <label key={f.id}>
            <input
              type="radio"
              name="statusFilter"
              checked={filter === f.id}
              onChange={() => setFilter(f.id)}
            />
            {f.label}
          </label>
        ))}
      </div>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : users.length === 0 ? (
        <p className="muted">No users found.</p>
      ) : (
        <ul className="history-list">
          {users.map((u) => (
            <li key={u.id} className="history-item">
              <div className="history-summary admin-user-row">
                <span>
                  <strong>{u.name}</strong> &lt;{u.email}&gt;
                </span>
                <span className="muted">{u.provider}</span>
                <span className={`status-badge status-${u.status}`}>{u.status}</span>
                <span className="muted">{new Date(u.created_at).toLocaleString()}</span>
              </div>
              {u.status !== 'approved' && (
                <div className="history-detail admin-actions">
                  <button type="button" onClick={() => handleApprove(u.id)}>
                    Approve
                  </button>
                  {u.status !== 'rejected' && (
                    <button type="button" className="btn-delete" onClick={() => handleReject(u.id)}>
                      Reject
                    </button>
                  )}
                </div>
              )}
              {u.status === 'approved' && (
                <div className="history-detail admin-actions">
                  <button type="button" className="btn-delete" onClick={() => handleReject(u.id)}>
                    Revoke
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
