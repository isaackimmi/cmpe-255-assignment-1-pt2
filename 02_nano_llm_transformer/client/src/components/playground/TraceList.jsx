import { displayToken, percentage } from "../../utils/format";

export function TraceList({ trace = [] }) {
  if (!trace.length) return <p className="empty">Selected characters will appear here with their context.</p>;
  return (
    <ol className="trace-list" aria-label="Generation trace">
      {trace.map((step) => (
        <li className="trace-row" key={step.step}>
          <b>{String(step.step).padStart(2, "0")}</b>
          <code>{step.context || "∅"}</code>
          <strong aria-label={`selected token ${displayToken(step.selected)}`}>{displayToken(step.selected)}</strong>
          <span>{(step.candidates || []).slice(0, 3).map((item) => `${displayToken(item.token)} ${percentage(item.probability)}`).join(" · ")}</span>
        </li>
      ))}
    </ol>
  );
}
