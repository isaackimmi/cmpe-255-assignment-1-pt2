export function AsyncState({ error, onRetry, title = "Unable to load this section" }) {
  if (!error) return null;
  return (
    <div className="async-error" role="alert">
      <div><strong>{title}</strong><p>{error.message}</p></div>
      <button type="button" onClick={onRetry}>Retry</button>
    </div>
  );
}
