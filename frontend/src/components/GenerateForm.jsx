import { useState } from 'react'
import { generateCoverLetter } from '../api/coverLetters'
import { uploadResume } from '../api/resumes'
import LoadingBar from './LoadingBar'
import ResultView from './ResultView'

const STEPS = [
  { id: 1, label: 'Resume' },
  { id: 2, label: 'Job details' },
  { id: 3, label: 'Result' },
]

export default function GenerateForm({ resumes, resumesError, onGenerated, onResumeUploaded, user }) {
  const [step, setStep] = useState(1)
  const [resumeMode, setResumeMode] = useState('upload')
  const [resumeLabel, setResumeLabel] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [savedResumeId, setSavedResumeId] = useState('')
  const [roleTitle, setRoleTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [genCoverLetter, setGenCoverLetter] = useState(true)
  const [genWtc, setGenWtc] = useState(false)
  const [loading, setLoading] = useState(false)
  const [justFinished, setJustFinished] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const isPdf = (f) =>
    f && (f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'))

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0] ?? null
    setError(selected && !isPdf(selected) ? 'Please select a PDF file.' : null)
    setResumeFile(selected)
  }

  const resumeReady =
    resumeMode === 'upload'
      ? resumeLabel.trim() && resumeFile && isPdf(resumeFile)
      : Boolean(savedResumeId)

  const detailsReady = Boolean(roleTitle.trim() && jobDescription.trim() && (genCoverLetter || genWtc))

  const atCap = !user?.is_admin && user?.generations_used >= user?.generation_limit

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!resumeReady || !detailsReady || loading) return

    setLoading(true)
    setError(null)
    try {
      let resumeId = Number(savedResumeId)
      if (resumeMode === 'upload') {
        const resume = await uploadResume({ label: resumeLabel.trim(), file: resumeFile })
        resumeId = resume.id
        onResumeUploaded()
      }

      const generated = await generateCoverLetter({
        resume_id: resumeId,
        role_title: roleTitle.trim(),
        job_description: jobDescription.trim(),
        generate_cover_letter: genCoverLetter,
        generate_why_this_company: genWtc,
      })
      setJustFinished(true)
      await new Promise((r) => setTimeout(r, 450))
      setResult(generated)
      setStep(3)
      onGenerated()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setJustFinished(false)
    }
  }

  const startOver = () => {
    setResult(null)
    setError(null)
    setStep(1)
  }

  const goToStep = (s) => {
    if (s < step && !loading) setStep(s)
  }

  return (
    <div className="panel">
      <h2>Generate Cover Letter</h2>

      {resumesError && <p className="error">Failed to load saved resumes: {resumesError}</p>}

      <ol className="wizard-steps">
        {STEPS.map((s) => (
          <li
            key={s.id}
            className={s.id === step ? 'active' : s.id < step ? 'done' : ''}
            onClick={() => goToStep(s.id)}
          >
            <span className="wizard-step-circle">{s.id}</span>
            <span className="wizard-step-label">{s.label}</span>
          </li>
        ))}
      </ol>

      {step === 1 && (
        <div className="form wizard-step-content">
          <div className="resume-mode-toggle">
            <label>
              <input
                type="radio"
                name="resumeMode"
                value="upload"
                checked={resumeMode === 'upload'}
                onChange={() => setResumeMode('upload')}
              />
              Upload a new resume
            </label>
            <label>
              <input
                type="radio"
                name="resumeMode"
                value="saved"
                checked={resumeMode === 'saved'}
                onChange={() => setResumeMode('saved')}
                disabled={resumes.length === 0}
              />
              Use a saved resume
            </label>
          </div>

          {resumeMode === 'upload' ? (
            <>
              <label>
                Resume label
                <input
                  type="text"
                  value={resumeLabel}
                  onChange={(e) => setResumeLabel(e.target.value)}
                  placeholder="e.g. Software Engineer Resume"
                />
              </label>

              <label>
                Resume PDF
                <input type="file" accept=".pdf,application/pdf" onChange={handleFileChange} />
              </label>
            </>
          ) : (
            <label>
              Saved resume
              <select value={savedResumeId} onChange={(e) => setSavedResumeId(e.target.value)}>
                <option value="">Select a saved resume...</option>
                {resumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.label}
                  </option>
                ))}
              </select>
            </label>
          )}

          {error && <p className="error">{error}</p>}

          <div className="wizard-actions">
            <button type="button" onClick={() => setStep(2)} disabled={!resumeReady}>
              Next
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <form onSubmit={handleGenerate} className="form wizard-step-content">
          <label>
            Role Title
            <input
              type="text"
              value={roleTitle}
              onChange={(e) => setRoleTitle(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
            />
          </label>

          <label>
            Job Description
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={8}
              placeholder="Paste the job description here..."
            />
          </label>

          <div className="output-options">
            <span className="output-options-label">Generate:</span>
            <label className="output-option">
              <input
                type="checkbox"
                checked={genCoverLetter}
                onChange={(e) => setGenCoverLetter(e.target.checked)}
                disabled={loading}
              />
              Cover Letter
            </label>
            <label className="output-option">
              <input
                type="checkbox"
                checked={genWtc}
                onChange={(e) => setGenWtc(e.target.checked)}
                disabled={loading}
              />
              Why This Company
            </label>
          </div>

          {!genCoverLetter && !genWtc && (
            <p className="error">Select at least one output to generate.</p>
          )}

          {atCap && (
            <p className="error">
              You&apos;ve reached your generation limit ({user.generations_used}/{user.generation_limit}).
              Contact an admin to request more.
            </p>
          )}

          {error && <p className="error">{error}</p>}

          <div className="wizard-actions wizard-actions-between">
            <button type="button" onClick={() => setStep(1)} disabled={loading}>
              Back
            </button>
            <button type="submit" disabled={!detailsReady || loading || atCap}>
              {loading ? 'Generating...' : 'Generate'}
            </button>
          </div>

          {loading && <LoadingBar complete={justFinished} />}
        </form>
      )}

      {step === 3 && (
        <div className="wizard-step-content">
          <ResultView result={result} />
          <div className="wizard-actions">
            <button type="button" onClick={startOver}>
              Start over
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
