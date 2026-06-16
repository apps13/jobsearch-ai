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
    if (user?.status === 'approved') loadResumes()
  }, [user])

  const handleLogout = async () => {
    await logout()
    setUser(null)
  }

  if (user === undefined) {
    return null
  }

  const tabs = user?.is_admin ? [...TABS, ADMIN_TAB] : TABS
  const { startTour } = useTour(user?.is_admin)

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-row">
          <div>
            <h1>JobSearch AI</h1>
            <p className="tagline">Tailored cover letters, fast.</p>
          </div>
          {user && (user.status === 'approved' || user.is_admin) && (
            <div className="header-actions">
              <button type="button" className="btn-help" onClick={startTour} title="Take a tour">
                ?
              </button>
              <button type="button" className="btn-delete" onClick={handleLogout}>
                Log out
              </button>
            </div>
          )}
          {user && user.status !== 'approved' && !user.is_admin && (
            <button type="button" className="btn-delete" onClick={handleLogout}>
              Log out
            </button>
          )}
        </div>
      </header>

      {!user && <LoginPage />}

      {user && user.status !== 'approved' && !user.is_admin && <PendingApproval status={user.status} />}

      {user && (user.status === 'approved' || user.is_admin) && (
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
              onGenerated={() => setHistoryRefreshKey((k) => k + 1)}
              onResumeUploaded={loadResumes}
            />
          )}

          {tab === 'history' && <HistoryList refreshKey={historyRefreshKey} />}

          {tab === 'admin' && user.is_admin && <AdminPanel />}
        </>
      )}
    </div>
  )
}

export default App
