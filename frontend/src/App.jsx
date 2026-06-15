import { useEffect, useState } from 'react'
import './App.css'
import { getResumes } from './api/resumes'
import GenerateForm from './components/GenerateForm'
import ResultView from './components/ResultView'
import HistoryList from './components/HistoryList'

const TABS = [
  { id: 'generate', label: 'Generate' },
  { id: 'history', label: 'History' },
]

function App() {
  const [tab, setTab] = useState('generate')
  const [resumes, setResumes] = useState([])
  const [resumesError, setResumesError] = useState(null)
  const [lastResult, setLastResult] = useState(null)
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0)

  const loadResumes = async () => {
    try {
      setResumes(await getResumes())
      setResumesError(null)
    } catch (err) {
      setResumesError(err.message)
    }
  }

  useEffect(() => {
    loadResumes()
  }, [])

  return (
    <div className="app">
      <h1>JobSearch AI</h1>
      <p className="tagline">Tailored cover letters, fast.</p>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={tab === t.id ? 'active' : ''}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {resumesError && <p className="error">Failed to load saved resumes: {resumesError}</p>}

      {tab === 'generate' && (
        <>
          <GenerateForm
            resumes={resumes}
            onResult={setLastResult}
            onGenerated={() => setHistoryRefreshKey((k) => k + 1)}
            onResumeUploaded={loadResumes}
          />
          <ResultView result={lastResult} />
        </>
      )}

      {tab === 'history' && <HistoryList refreshKey={historyRefreshKey} />}
    </div>
  )
}

export default App
