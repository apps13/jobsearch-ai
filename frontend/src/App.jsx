import { useEffect, useState } from 'react'
import './App.css'
import { getCurrentUser, logout } from './api/auth'
import { getResumes } from './api/resumes'
import AdminPanel from './components/AdminPanel'
import GenerateForm from './components/GenerateForm'
import HistoryList from './components/HistoryList'
import LoginPage from './components/LoginPage'
import PendingApproval from './components/PendingApproval'
import { useTour } from './hooks/useTour'

const TABS = [
  { id: 'generate', label: 'Generate' },
  { id: 'history', label: 'History' },
]

const ADMIN_TAB = { id: 'admin', label: 'Admin' }

function App() {
  const [tab, setTab] = useState('generate')
  const [resumes, setResumes] = useState([])
  const [resumesError, setResumesError] = useState(null)
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0)
  const [user, setUser] = useState(undefined)

  const loadResumes = async () => {
    try {
      setResumes(await getResumes())
      setResumesError(null)
    } catch (err) {
      setResumesError(err.message)
    }
  }

  const loadUser = async () => {
    try {
      setUser(await getCurrentUser())
    } catch {
      setUser(null)
    }
  }

  useEffect(() => {
    loadUser()
  }, [])

  useEffect(() => {
    if (user && user.status !== 'rejected') loadResumes()
  }, [user])

  const handleLogout = async () => {
    await logout()
    setUser(null)
  }

  const { startTour } = useTour(user?.is_admin)
  const tabs = user?.is_admin ? [...TABS, ADMIN_TAB] : TABS

  if (user === undefined) {
    return null
  }

  return (
    <div className="app-wrapper">
      <header className="app-header">
        <div className="app-header-row">
          <span className="app-brand">JobSearch AI</span>
          {user && (
            <div className="header-actions">
              {user.email && (
                <span className="header-user">{user.email}</span>
              )}
              {(user.status !== 'rejected' || user.is_admin) && (
                <button type="button" className="btn-help" onClick={startTour} title="Take a tour">
                  ?
                </button>
              )}
              <button type="button" className="btn-logout" onClick={handleLogout}>
                Log out
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="app">
        {!user && <LoginPage />}

        {user && user.status === 'rejected' && !user.is_admin && <PendingApproval />}

        {user && (user.status !== 'rejected' || user.is_admin) && (
          <>
            <nav className="tabs">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  className={tab === t.id ? 'active' : ''}
                  onClick={() => setTab(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </nav>

            {tab === 'generate' && (
              <GenerateForm
                resumes={resumes}
                resumesError={resumesError}
                onGenerated={() => {
                  setHistoryRefreshKey((k) => k + 1)
                  loadUser()
                }}
                onResumeUploaded={loadResumes}
                user={user}
              />
            )}

            {tab === 'history' && <HistoryList refreshKey={historyRefreshKey} />}

            {tab === 'admin' && user.is_admin && <AdminPanel />}
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>© 2026 JobSearch AI. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default App
