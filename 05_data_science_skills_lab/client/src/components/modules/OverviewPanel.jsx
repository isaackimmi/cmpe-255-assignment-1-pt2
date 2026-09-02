import { Panel } from "../common/Panel";

export function OverviewPanel({ metrics }) {
  const quality = metrics.data_quality;
  return <div className="detail-grid"><Panel large><span className="tag">PIPELINE MAP</span><div className="pipeline"><span>CSV ingest</span><i>→</i><span>validate + clean</span><i>→</i><span>fit boundaries</span><i>→</i><span>evaluate</span></div><p className="callout">Five modules share one validated fixture, but each uses an appropriate DS protocol: stratified classification, continuous regression, descriptive EDA, and scaled unsupervised clustering.</p></Panel><Panel><span className="tag">RUN CONTEXT</span><h3>Seeded, offline, inspectable</h3><dl><dt>Input rows</dt><dd>{quality.raw_rows}</dd><dt>Fixture</dt><dd>synthetic CSV</dd><dt>Seed</dt><dd>{metrics.reproducibility.seed}</dd><dt>Methods</dt><dd>standard library</dd></dl></Panel></div>;
}
