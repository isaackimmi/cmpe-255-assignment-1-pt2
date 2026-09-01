import { ModuleNav } from "../navigation/ModuleNav";

export function Sidebar({ activeModule, onSelect }) {
  return <aside className="sidebar">
    <div className="brand"><span className="brand-mark">05</span><div><b>signal/</b><small>DATA SCIENCE SKILLS LAB</small></div></div>
    <p className="eyebrow">CRISP-DM WORKBENCH</p>
    <ModuleNav activeModule={activeModule} onSelect={onSelect}/>
    <div className="sidebar-note"><span className="pulse"/><b>Offline artifact mode</b><small>FastAPI serves checked-in experiment evidence. No browser-side model fitting.</small></div>
  </aside>;
}
