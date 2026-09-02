export function Sidebar({ project, profile }) {
  return (
    <aside className="sidebar">
      <div className="brand"><span>✦</span> fieldnote</div>
      <p className="eyebrow">Workspace</p>
      <nav className="side-nav" aria-label="Workspace navigation">
        <button className="active" type="button" aria-current="page">▦ &nbsp; Overview</button>
        <span className="planned-nav-item">◌ &nbsp; Agent runs <small>planned · no connected run</small></span>
        <span className="planned-nav-item">⌁ &nbsp; Datasets <small>planned · no connected dataset</small></span>
      </nav>
      <div className="project">
        <p className="eyebrow">Active project</p>
        <strong>{project.name}</strong>
        <small>{project.goal}</small>
      </div>
      <div className="profile">
        <div className="avatar" aria-hidden="true">{profile.initials}</div>
        <div><strong>{profile.name}</strong><small>{profile.role}</small></div>
      </div>
    </aside>
  );
}
