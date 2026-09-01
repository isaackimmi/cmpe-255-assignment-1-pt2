export function AppHeader({ status }) {
  return (
    <header className="topbar">
      <div className="brand"><span className="mark">03</span><div><strong>Segment Atlas</strong><small>Customer clustering laboratory</small></div></div>
      <div className="status" role="status" aria-live="polite">{status}</div>
    </header>
  );
}
