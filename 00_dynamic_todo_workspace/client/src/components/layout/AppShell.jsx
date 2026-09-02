import { Sidebar } from "./Sidebar";

export function AppShell({ workspace, profile, children }) {
  return (
    <div className="shell">
      <Sidebar project={workspace.project} profile={profile} />
      <main className="main">
        <div className="mobile-brand" aria-label="Fieldnote workspace">✦ fieldnote <span>Overview</span></div>
        <div className="topbar">
          <span>Projects / {workspace.project.name}</span>
          <span className="api-connected">● API connected</span>
        </div>
        {children}
      </main>
    </div>
  );
}
