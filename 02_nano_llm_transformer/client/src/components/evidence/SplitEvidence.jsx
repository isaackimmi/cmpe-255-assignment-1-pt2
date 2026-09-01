import { Panel } from "../ui";

export function SplitEvidence({ split = {} }) {
  const keys = ["train", "validation", "test"];
  const total = keys.reduce((sum, key) => sum + Number(split[`${key}_chars`] || 0), 0);
  const summary = keys.map((key) => `${key} ${split[`${key}_chars`] ?? 0} characters`).join(", ");
  return (
    <Panel className="split-panel">
      <p className="kicker">DATA CONTRACT</p>
      <h2>One corpus, three honest splits.</h2>
      <figure className="split-figure">
        <div className="split-bar" role="group" aria-label="Chronological corpus split">
          {keys.map((key) => {
            const percent = total ? Number(split[`${key}_chars`] || 0) / total * 100 : 0;
            return <span key={key} role="meter" aria-label={`${key} portion`} aria-valuemin="0" aria-valuemax="100" aria-valuenow={Math.round(percent)} className={`split-${key}`} style={{ width: `${percent}%` }} />;
          })}
        </div>
        <figcaption className="sr-only">{summary}</figcaption>
      </figure>
      <div className="split-labels">
        {keys.map((key) => <span key={key}>{key.toUpperCase()} <b>{split[`${key}_chars`] ?? "—"}</b></span>)}
      </div>
      <p className="annotation">The vocabulary is fitted on training characters only. Unseen validation/test characters map to <code>&lt;UNK&gt;</code>; the test suffix is evaluated once after model selection.</p>
    </Panel>
  );
}
