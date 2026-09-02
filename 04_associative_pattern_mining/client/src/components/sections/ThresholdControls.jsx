import { RangeControl } from "../ui/RangeControl";
import { SectionHeader } from "../ui/SectionHeader";
import { percent } from "../../utils/format";

export function ThresholdControls({ filters, summary, onChange }) {
  return (
    <section className="section" id="thresholds">
      <SectionHeader
        eyebrow="01 / MODEL CONTROLS"
        title={<>Turn the dials.<br /><em>Watch the evidence move.</em></>}
        note="The client queries FastAPI; the server reruns the same audited Apriori and rule-metric functions used by the Python experiment."
      />
      <div className="control-panel">
        <RangeControl id="support" label="Minimum support" value={filters.support * 100} displayValue={percent(filters.support)} min={5} max={100} step={5} help="prevalence across all baskets" onChange={(value) => onChange("support", value / 100)} />
        <RangeControl id="confidence" label="Minimum confidence" value={filters.confidence * 100} displayValue={percent(filters.confidence)} min={5} max={100} step={5} help="share of antecedent baskets" onChange={(value) => onChange("confidence", value / 100)} />
        <RangeControl id="count" label="Minimum basket count" value={filters.count} displayValue={filters.count} min={1} max={24} step={1} help="absolute denominator guardrail" onChange={(value) => onChange("count", value)} />
        <div className="control-result"><strong>{summary?.effective_support_count ?? "—"}</strong><span>effective count floor<br /><small>{summary ? `${percent(summary.effective_support)} effective support` : "—"}</small></span></div>
      </div>
    </section>
  );
}
