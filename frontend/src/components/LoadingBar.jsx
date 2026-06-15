export default function LoadingBar({ complete }) {
  return (
    <div className="loading-bar">
      <div className="loading-bar-track">
        <div className={`loading-bar-fill${complete ? ' complete' : ''}`} />
      </div>
      <p className="loading-bar-label">
        {complete ? 'Done!' : 'Generating your cover letter...'}
      </p>
    </div>
  )
}
