import { useState } from 'react'

function CopyButton({ getText }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(getText())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button type="button" className="btn-copy" onClick={handleCopy}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

function CoverLetterText({ coverLetter }) {
  const getText = () =>
    [
      coverLetter.greeting,
      coverLetter.opening_paragraph,
      coverLetter.body_paragraph_1,
      coverLetter.body_paragraph_2,
      coverLetter.closing_paragraph,
      coverLetter.sign_off,
    ].join('\n\n')

  return (
    <div className="cover-letter-text">
      <div className="result-section-header">
        <CopyButton getText={getText} />
      </div>
      <p>{coverLetter.greeting}</p>
      <p>{coverLetter.opening_paragraph}</p>
      <p>{coverLetter.body_paragraph_1}</p>
      <p>{coverLetter.body_paragraph_2}</p>
      <p>{coverLetter.closing_paragraph}</p>
      <p>{coverLetter.sign_off}</p>
    </div>
  )
}

function WhyThisCompany({ text }) {
  return (
    <div className="why-this-company">
      <div className="result-section-header">
        <CopyButton getText={() => text} />
      </div>
      <p>{text}</p>
    </div>
  )
}

function FitAnalysisBlock({ fitAnalysis }) {
  return (
    <div className="fit-analysis">
      <h4>Fit Analysis</h4>
      <p>
        <strong>Match score:</strong>{' '}
        <span className="match-score">{fitAnalysis.match_score}%</span>
      </p>
      <p>
        <strong>Matched skills:</strong>
      </p>
      <ul className="matched-skills">
        {fitAnalysis.matched_skills.map((skill) => (
          <li key={skill}>{skill}</li>
        ))}
      </ul>
      <p>
        <strong>Gaps:</strong>
      </p>
      <ul className="gaps">
        {fitAnalysis.gaps.map((gap) => (
          <li key={gap}>{gap}</li>
        ))}
      </ul>
      <p>
        <strong>Recommendation:</strong> {fitAnalysis.recommendation}
      </p>
    </div>
  )
}

export default function ResultView({ result }) {
  const [activeTab, setActiveTab] = useState('cover-letter')

  if (!result) {
    return <p className="muted">No result yet — generate a cover letter to see it here.</p>
  }

  const hasCoverLetter = Boolean(result.cover_letter)
  const hasWtc = Boolean(result.why_this_company)
  const showTabs = hasCoverLetter && hasWtc

  return (
    <div className="result-view">
      {result.fit_analysis && <FitAnalysisBlock fitAnalysis={result.fit_analysis} />}

      {showTabs && (
        <>
          <div className="result-tabs">
            <button
              type="button"
              className={activeTab === 'cover-letter' ? 'active' : ''}
              onClick={() => setActiveTab('cover-letter')}
            >
              Cover Letter
            </button>
            <button
              type="button"
              className={activeTab === 'why-this-company' ? 'active' : ''}
              onClick={() => setActiveTab('why-this-company')}
            >
              Why This Company
            </button>
          </div>
          {activeTab === 'cover-letter' && <CoverLetterText coverLetter={result.cover_letter} />}
          {activeTab === 'why-this-company' && <WhyThisCompany text={result.why_this_company} />}
        </>
      )}

      {!showTabs && hasCoverLetter && <CoverLetterText coverLetter={result.cover_letter} />}
      {!showTabs && hasWtc && <WhyThisCompany text={result.why_this_company} />}
    </div>
  )
}

export { CoverLetterText, FitAnalysisBlock as FitAnalysis }
