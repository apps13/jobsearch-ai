import { API_URL } from '../api/client'

const PROVIDERS = [
  { id: 'google', label: 'Continue with Google' },
  { id: 'microsoft', label: 'Continue with Microsoft' },
]

export default function LoginPage() {
  return (
    <div className="panel login-panel">
      <h2>Sign in</h2>
      <p className="muted">Sign in to generate tailored cover letters.</p>
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
