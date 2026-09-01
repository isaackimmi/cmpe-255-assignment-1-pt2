import { Panel, StatusPill } from "../ui";
import { ProbabilityPanel } from "./ProbabilityPanel";
import { TraceList } from "./TraceList";

export function BehaviorInspector({ replay, metrics }) {
  const first = replay?.trace?.[0];
  const trace = replay?.trace || [];
  return (
    <Panel className="behavior-card">
      <div className="chat-head">
        <strong>Behavior inspector</strong>
        <StatusPill>{replay ? (replay.deterministic ? "DETERMINISTIC" : "REPLAY") : "WAITING"}</StatusPill>
      </div>
      <section className="context-card" aria-labelledby="context-window-label">
        <span id="context-window-label">LAST CONTEXT WINDOW</span>
        <code>{first?.context || "—"}</code>
        <small>order {replay?.context_order ?? metrics?.behavior?.order ?? metrics?.config?.order ?? "—"}</small>
      </section>
      <ProbabilityPanel candidates={first?.candidates} />
      <div className="subhead trace-heading"><span>GENERATION TRACE</span><small>{trace.length} steps</small></div>
      <TraceList trace={trace} />
    </Panel>
  );
}
