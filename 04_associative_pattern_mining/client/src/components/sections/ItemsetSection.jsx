import { ItemsetList } from "../data/ItemsetList";
import { SelectField } from "../ui/SelectField";
import { SectionHeader } from "../ui/SectionHeader";

const SIZE_OPTIONS = [{ value: "", label: "All sizes" }, { value: "2", label: "Pairs" }, { value: "3", label: "Triples" }];

export function ItemsetSection({ rows, transactionCount, size, onSizeChange, loading }) {
  const action = <SelectField label="Pattern size" value={size} options={SIZE_OPTIONS} onChange={onSizeChange} />;
  return (
    <section className="section chart-layout">
      <div>
        <SectionHeader eyebrow="02 / ITEMSETS" title="Prevalence, made legible." action={action} compact />
        <div className="chart card">
          {loading ? <p className="loading">Loading itemsets…</p> : <ItemsetList rows={rows} transactionCount={transactionCount} />}
        </div>
        <p className="source-note">Support = baskets containing the itemset / {transactionCount ?? "—"} total baskets.</p>
      </div>
      <aside className="explain card">
        <p className="eyebrow">WHY IT MATTERS</p><h3>Support is the prevalence guardrail.</h3>
        <p>A pattern can have impressive confidence simply because its consequent is popular. Start with support to make the denominator visible, then use confidence and lift to qualify the relationship.</p>
        <div className="formula"><span>support</span><strong>count(itemset) / n baskets</strong></div>
        <div className="formula"><span>lift</span><strong>confidence / support(consequent)</strong></div>
      </aside>
    </section>
  );
}
