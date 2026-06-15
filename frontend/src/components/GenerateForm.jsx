import { useState } from 'react'
import { generateCoverLetter } from '../api/coverLetters'
import { uploadResume } from '../api/resumes'
import LoadingBar from './LoadingBar'

export default function GenerateForm({ resumes, onResult, onGenerated, onResumeUploaded }) {
  const [resumeMode, setResumeMode] = useState('upload')
  const [resumeLabel, setResumeLabel] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [savedResumeId, setSavedResumeId] = useState('')
  const [roleTitle, setRoleTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [justFinished, setJustFinished] = useState(false)
  const [error, setError] = useState(null)

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

  const canSubmit = resumeReady && roleTitle.trim() && jobDescription.trim() && !loading

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!canSubmit) return

    setLoading(true)
    setError(null)
    try {
      let resumeId = Number(savedResumeId)
      if (resumeMode === 'upload') {
        const resume = await uploadResume({ label: resumeLabel.trim(), file: resumeFile })
        resumeId = resume.id
        onResumeUploaded()
      }

      const result = await generateCoverLetter({
        resume_id: resumeId,
        role_title: roleTitle.trim(),
        job_description: jobDescription.trim(),
      })
      setJustFinished(true)
      await new Promise((r) => setTimeout(r, 450))
      onResult(result)
      onGenerated()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setJustFinished(false)
    }
  }

  return (
    <div className="panel">
      <h2>Generate Cover Letter</h2>

      <form onSubmit={handleSubmit} className="form">
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

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={!canSubmit}>
          {loading ? 'Generating...' : 'Generate'}
        </button>

        {loading && <LoadingBar complete={justFinished} />}
      </form>
    </div>
  )
}
