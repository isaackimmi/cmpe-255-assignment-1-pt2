import { Badge } from "@radix-ui/themes";

const labels = {
  connecting: "● connecting",
  connected: "● API connected",
  partial: "● API connected · partial evidence",
  unavailable: "● API unavailable",
};

export function TopBar({ status }) {
  return (
    <header className="topbar">
      <a className="brand" href="#top" aria-label="Nano LLM home">
        <span className="mark">N</span>nano<span className="orange">/llm</span>
      </a>
      <nav aria-label="Primary navigation">
        <a href="#evidence">Evidence</a>
        <a href="#playground">Replay</a>
        <a href="#method">Method</a>
      </nav>
      <Badge className={`status status-${status}`} color={status === "unavailable" ? "red" : status === "partial" ? "orange" : "lime"} role="status" aria-live="polite" aria-atomic="true">
        {labels[status] || labels.connecting}
      </Badge>
    </header>
  );
}
