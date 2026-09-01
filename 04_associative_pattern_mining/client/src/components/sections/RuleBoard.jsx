import { SelectField } from "../ui/SelectField";
import { SectionHeader } from "../ui/SectionHeader";
import { decimal, percent, rank } from "../../utils/format";

const SORT_OPTIONS = [{ value: "lift", label: "Lift" }, { value: "confidence", label: "Confidence" }, { value: "support", label: "Support" }];

function RuleCard({ row, index, transactionCount }) {
  return (
    <article className="rule-card">
      <span className="rank">{rank(index)} · exploratory rule</span><h3>{row.label}</h3>
      <div className="rule-metrics">
        <div><span>Support</span><strong>{percent(row.support)}</strong><small>{Math.round(row.support_count)}/{transactionCount} baskets</small></div>
        <div><span>Confidence</span><strong>{percent(row.confidence)}</strong><small>antecedent conditional</small></div>
        <div><span>Lift</span><strong>{decimal(row.lift)}×</strong><small>vs independence</small></div>
      </div>
    </article>
  );
}

export function RuleBoard({ rows, transactionCount, sort, onSortChange, loading }) {
  return (
    <section className="section" id="rules">
      <SectionHeader
        eyebrow="03 / RULE BOARD"
        title="Signals worth a closer look."
        action={<SelectField label="Sort by" value={sort} options={SORT_OPTIONS} onChange={onSortChange} />}
      />
      <p className="section-note">Exploratory, in-sample rules. Every card keeps the absolute support and antecedent denominator visible.</p>
      <div className="rule-grid">
        {loading ? <p className="loading">Loading rules…</p> : rows.length ? rows.slice(0, 12).map((row, index) => <RuleCard key={row.label} row={row} index={index} transactionCount={transactionCount} />) : <p className="empty">No rules meet the active thresholds.</p>}
      </div>
    </section>
  );
}
