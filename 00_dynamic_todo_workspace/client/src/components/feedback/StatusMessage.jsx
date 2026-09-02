export function StatusMessage({ message }) {
  return <div className="status-message" role="status" aria-live="polite">{message}</div>;
}
