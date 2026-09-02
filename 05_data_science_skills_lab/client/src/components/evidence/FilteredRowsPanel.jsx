import Chip from "@mui/material/Chip";

const filterLabels = { plan: "Plan", renewal: "Renewal", cluster: "Cluster" };

export function FilteredRowsPanel({ rowsResult, filters, updating }) {
  const active = Object.entries(filters).filter(([, value]) => value !== "all");
  return <section className="filtered-rows" aria-labelledby="filtered-rows-title">
    <div className="filtered-rows__header">
      <div><span className="tag">FILTERED ROW EVIDENCE</span><h3 id="filtered-rows-title">Rows matching the global filters</h3></div>
      <strong aria-live="polite">{updating ? "Updating…" : `${rowsResult.count} rows`}</strong>
    </div>
    <div className="filtered-rows__chips" aria-label="Active filters">
      {active.length ? active.map(([name, value]) => <Chip key={name} size="small" label={`${filterLabels[name]}: ${value}`}/>) : <Chip size="small" label="All rows"/>}
    </div>
    <p className="filtered-rows__note">These controls filter the row evidence only. Headline, holdout, classification, regression, and clustering metrics remain fixed checked-in artifact metrics; the API does not re-score subgroups.</p>
    <div className="table-scroll"><table className="evidence-table"><caption>Customer rows returned by the current server-side filters</caption><thead><tr><th scope="col">Customer</th><th scope="col">Plan</th><th scope="col">Renewed</th><th scope="col">Cluster</th><th scope="col">Usage</th></tr></thead><tbody>{rowsResult.rows.slice(0, 8).map((row) => <tr key={row.customer_id}><th scope="row">{row.customer_id}</th><td>{row.plan}</td><td>{row.renewed ? "Yes" : "No"}</td><td>{row.cluster}</td><td>{row.monthly_usage ?? "Missing"}</td></tr>)}</tbody></table></div>
  </section>;
}
