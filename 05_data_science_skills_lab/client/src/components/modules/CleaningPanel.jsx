import { Panel, PanelHeader } from "../common/Panel";

export function CleaningPanel({ metrics }) {
  const quality = metrics.data_quality;
  return <div className="detail-grid"><Panel large><PanelHeader tag="DATA QUALITY CONTRACT" value={`${quality.clean_rows} clean rows`}/><div className="quality-grid">{Object.entries(quality.missing_values_by_column).map(([key, value]) => <div key={key}><span>{key}</span><b>{value} missing</b><small>{value ? "median-imputed where permitted" : "complete"}</small></div>)}</div><p className="callout">{quality.validation}. Duplicate IDs are accepted only when records are identical.</p></Panel><Panel><span className="tag">IMPUTATION</span><h3>Fit scope matters</h3><p>Global descriptive views use explicit medians. Predictive transforms fit medians on training rows and reuse them on the holdout.</p><dl><dt>Rows read</dt><dd>{quality.raw_rows}</dd><dt>Duplicates removed</dt><dd>{quality.duplicates_removed}</dd><dt>Values imputed</dt><dd>{quality.missing_values_imputed}</dd></dl></Panel></div>;
}
