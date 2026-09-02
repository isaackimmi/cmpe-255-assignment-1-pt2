function StatusBadge({ status }) {
  return <span className={`status status-${status.tone}`} role="status"><i /> {status.label}</span>;
}

export function AppShell({ status, children }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top"><span className="brand-mark">✦</span><span>basket<span className="muted">.</span>signals</span></a>
        <StatusBadge status={status} />
        <span className="project-tag">CMPE 255 · PROJECT 04</span>
      </header>
      <main id="top">{children}</main>
      <footer>
        <span>basket<span className="muted">.</span>signals</span>
        <span>FastAPI + React · local evidence workbench</span>
        <span>synthetic/local fixture · no production claims</span>
      </footer>
    </div>
  );
}
