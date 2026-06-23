import { useEffect, useState } from 'react'
import { blockUser, listUsers, unblockUser, updateGenerationLimit } from '../api/admin'

export default function AdminPanel() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editValue, setEditValue] = useState('')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setUsers(await listUsers())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleBlock = async (id) => {
    try {
      await blockUser(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleUnblock = async (id) => {
    try {
      await unblockUser(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const startEdit = (u) => {
    setEditingId(u.id)
    setEditValue(String(u.generation_limit))
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditValue('')
  }

  const saveEdit = async (id) => {
    const limit = Number(editValue)
    if (!Number.isInteger(limit) || limit < 0) {
      setError('Limit must be a non-negative whole number.')
      return
    }
    try {
      await updateGenerationLimit(id, limit)
      cancelEdit()
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

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : users.length === 0 ? (
        <p className="muted">No users found.</p>
      ) : (
        <ul className="history-list">
          {users.map((u) => {
            const blocked = u.status === 'rejected'
            const atCap = u.generations_used >= u.generation_limit
            return (
              <li key={u.id} className="history-item">
                <div className="history-summary admin-user-row">
                  <span>
                    <strong>{u.name}</strong> &lt;{u.email}&gt;
                  </span>
                  <span className="muted">{u.provider}</span>
                  <span className={`status-badge ${atCap ? 'status-rejected' : 'status-approved'}`}>
                    {u.generations_used} / {u.generation_limit}
                  </span>
                  {blocked && <span className="status-badge status-rejected">blocked</span>}
                  <span className="muted admin-timestamp">{new Date(u.created_at).toLocaleString()}</span>
                </div>
                <div className="history-detail admin-actions">
                  {editingId === u.id ? (
                    <>
                      <input
                        type="number"
                        min="0"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        style={{ width: '4.5em' }}
                      />
                      <button type="button" onClick={() => saveEdit(u.id)}>
                        Save
                      </button>
                      <button type="button" className="btn-delete" onClick={cancelEdit}>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button type="button" onClick={() => startEdit(u)}>
                      Edit limit
                    </button>
                  )}
                  {blocked ? (
                    <button type="button" onClick={() => handleUnblock(u.id)}>
                      Unblock
                    </button>
                  ) : (
                    <button type="button" className="btn-delete" onClick={() => handleBlock(u.id)}>
                      Block
                    </button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
