import { BarList } from "../ui/BarList";
import { SelectField } from "../ui/SelectField";
import { SectionHeader } from "../ui/SectionHeader";
import { AsyncState } from "../ui/AsyncState";

export function BasketExplorer({ items, selectedItem, context, onItemChange, loading, error, onRetry }) {
  const options = items.map((item) => ({ value: item, label: item }));
  return (
    <section className="section explorer">
      <SectionHeader
        eyebrow="04 / BASKET EXPLORER"
        title="Put a basket under the lens."
        note="Select a product to inspect its local co-occurrence context. This is not a rule; it is a conditional view for exploration."
      />
      <AsyncState error={error} onRetry={onRetry} title="Unable to load basket context" />
      <div className="explorer-grid">
        <div className="card basket-card">
          <p className="eyebrow">SELECTED ITEM</p>
          {options.length > 0 && <SelectField label="Product" value={selectedItem} options={options} onChange={onItemChange} />}
          <div className="big-item">{selectedItem}</div>
          <p><strong>{context?.basket_count ?? "—"}</strong> baskets contain this item.</p>
          <div className="item-chips">{context?.candidates.slice(0, 4).map((row) => <span key={row.item}>{row.item}</span>)}</div>
        </div>
        <div className="card context-card">
          <div className="card-title"><h3>What appears with it?</h3><span>P(candidate | item)</span></div>
          <div>
            {loading ? <p className="loading">Loading item context…</p> : <BarList rows={context?.candidates.slice(0, 8) || []} emptyMessage="No co-occurring items." labelFor={(row) => row.item} valueFor={(row) => row.conditional_probability} countFor={(row) => `${row.count}/${context?.basket_count}`} />}
          </div>
        </div>
      </div>
    </section>
  );
}
