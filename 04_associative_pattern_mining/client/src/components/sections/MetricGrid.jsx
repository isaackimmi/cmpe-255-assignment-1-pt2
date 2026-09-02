import { MetricCard } from "../ui/MetricCard";
import { decimal } from "../../utils/format";

export function MetricGrid({ summary, topRule }) {
  return (
    <section className="stats" aria-label="Run summary">
      <MetricCard label="TRANSACTIONS" value={summary?.transactions} note="source baskets" />
      <MetricCard label="ITEM UNIVERSE" value={summary?.items} note="unique products in source" />
      <MetricCard
        label="FREQUENT ITEMSETS"
        value={summary?.frequent_itemsets}
        note={summary ? `${summary.effective_support_count}/${summary.transactions} basket floor` : "under current thresholds"}
      />
      <MetricCard
        label="TOP LIFT"
        value={topRule ? `${decimal(topRule.lift)}×` : "—"}
        note={topRule?.label || "waiting for rules"}
        accent
      />
    </section>
  );
}
