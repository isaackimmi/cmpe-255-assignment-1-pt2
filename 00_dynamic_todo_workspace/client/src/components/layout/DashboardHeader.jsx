import { Button } from "../ui/Button";

export function DashboardHeader({ project, content, busy, checking, onAgentCheck }) {
  return (
    <section className="heading">
      <div>
        <p className="eyebrow">{content.eyebrow}</p>
        <h1>{content.titleLead} <em>{content.titleEmphasis}</em> {content.titleTail}</h1>
        <p className="lede">{content.description}</p>
      </div>
      <Button disabled={busy} onClick={onAgentCheck} aria-label={`Run a demo check for ${project.name}`}>
        ✦ {checking ? "Checking…" : "Simulate agent check"}
      </Button>
    </section>
  );
}
