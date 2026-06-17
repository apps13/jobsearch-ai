import { API_URL } from '../api/client'

const PROVIDERS = [
  { id: 'google', label: 'Continue with Google' },
  { id: 'microsoft', label: 'Continue with Microsoft' },
]

export default function LoginPage() {
  return (
    <div className="panel login-panel">
      <h2>JobSearch AI</h2>
      <p className="tagline">From resume to applications, tailored for you.</p>
      <p className="muted" style={{ marginTop: '0.75rem' }}>Sign in to get started.</p>
      <div className="login-buttons">
        {PROVIDERS.map((p) => (
          <a key={p.id} className="login-button" href={`${API_URL}/api/auth/${p.id}/login`}>
            {p.label}
          </a>
        ))}
      </div>
    </div>
  )
}
