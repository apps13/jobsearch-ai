function CoverLetterText({ coverLetter }) {
  return (
    <div className="cover-letter-text">
      <p>{coverLetter.greeting}</p>
      <p>{coverLetter.opening_paragraph}</p>
      <p>{coverLetter.body_paragraph_1}</p>
      <p>{coverLetter.body_paragraph_2}</p>
      <p>{coverLetter.closing_paragraph}</p>
      <p>{coverLetter.sign_off}</p>
    </div>
  )
}

function FitAnalysis({ fitAnalysis }) {
  return (
    <div className="fit-analysis">
      <h4>Fit Analysis</h4>
      <p>
        <strong>Match score:</strong> <span className="match-score">{fitAnalysis.match_score}%</span>
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
  if (!result) {
    return <p className="muted">No result yet — generate a cover letter to see it here.</p>
  }

  return (
    <div className="result-view">
      <h3>Cover Letter</h3>
      <CoverLetterText coverLetter={result.cover_letter} />
      <FitAnalysis fitAnalysis={result.fit_analysis} />
    </div>
  )
}

export { CoverLetterText, FitAnalysis }
