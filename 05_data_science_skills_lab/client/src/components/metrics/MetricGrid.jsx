import { MetricCard } from "../common/MetricCard";
import { number, percent } from "../../utils/format";

export function MetricGrid({ metrics }) {
  if (!metrics) return null;
  return <section className="metrics" aria-label="Headline metrics">
    <MetricCard label="CLEAN ROWS" value={metrics.data_quality.clean_rows} note={`${metrics.data_quality.duplicates_removed} duplicate removed`} accent/>
    <MetricCard label="CLASSIFICATION F1" value={number(metrics.classification.f1)} note={`accuracy ${percent(metrics.classification.accuracy)}`}/>
    <MetricCard label="REGRESSION MAE" value={number(metrics.regression.mae)} note={`baseline ${number(metrics.regression.mean_baseline_mae)}`}/>
    <MetricCard label="CLUSTER SILHOUETTE" value={number(metrics.clustering.silhouette)} note={`${metrics.clustering.k} interpretable groups`}/>
  </section>;
}
