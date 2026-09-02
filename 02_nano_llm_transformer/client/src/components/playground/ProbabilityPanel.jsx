import { ProbabilityList } from "./ProbabilityList";

export function ProbabilityPanel({ candidates = [] }) {
  return (
    <section aria-label="Next-character probabilities">
      <div className="subhead">
        <span>NEXT-CHARACTER PROBABILITIES</span>
        <small>{candidates.length ? `${candidates.length} candidates` : "—"}</small>
      </div>
      <ProbabilityList candidates={candidates} />
    </section>
  );
}
