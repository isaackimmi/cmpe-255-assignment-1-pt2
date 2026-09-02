import { Sidebar } from "./Sidebar";

export function AppShell({ activeModule, onSelectModule, status, ready, children }) {
  return <div className="app-shell">
    <Sidebar activeModule={activeModule} onSelect={onSelectModule}/>
    <main>
      <header className="topbar"><span>PROJECT 05 / ANALYTICS LAB</span><span className={`status${ready ? " ready" : ""}`} aria-live="polite">{status}</span></header>
      {children}
    </main>
  </div>;
}
