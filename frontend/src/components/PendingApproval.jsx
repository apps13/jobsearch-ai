export default function PendingApproval({ status }) {
  return (
    <div className="panel">
      <h2>{status === 'rejected' ? 'Access not approved' : 'Pending approval'}</h2>
      {status === 'rejected' ? (
        <p className="muted">
          Your account request was not approved. If you think this is a mistake, contact the
          site admin.
        </p>
      ) : (
        <p className="muted">
          Thanks for signing in! Your account is awaiting admin approval. Check back soon.
        </p>
      )}
    </div>
  )
}
