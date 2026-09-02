import { formatNumber } from "../../utils/format";
import { MetricCard } from "../common/MetricCard";

export function MetricGrid({ summary }) {
  if (!summary) return <section className="metrics" aria-busy="true" />;
  const metrics = [
    ["SELECTED MODEL", `K-Means · k=${summary.selected_k}`, `${summary.selected_preprocessing} · ${summary.n_customers} customers`],
    ["HELD-OUT SILHOUETTE", formatNumber(summary.validation.silhouette_mean, 4), `± ${formatNumber(summary.validation.silhouette_std, 4)}`],
    ["STABILITY ARI", formatNumber(summary.validation.stability_ari_mean, 4), "across repeated partitions"],
    ["FULL-SAMPLE SILHOUETTE", formatNumber(summary.fit_metrics.silhouette, 4), "descriptive diagnostic"],
  ];
  return <section className="metrics" aria-label="Model metrics">{metrics.map(([label, value, note]) => <MetricCard key={label} label={label} value={value} note={note} />)}</section>;
}
