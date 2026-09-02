import { FEATURES } from "../../constants/features";
import { formatNumber } from "../../utils/format";

export function ExplorerDataTable({ points, selectedId, onSelect, xFeature, yFeature }) {
  return (
    <details className="data-alternative">
      <summary>Accessible point data ({points.length} customers)</summary>
      <div className="table-scroll">
        <table>
          <caption>Non-visual alternative to the customer scatter plot</caption>
          <thead><tr><th scope="col">Customer</th><th scope="col">Segment</th><th scope="col">{FEATURES[xFeature]}</th><th scope="col">{FEATURES[yFeature]}</th><th scope="col">Assignment</th><th scope="col">Margin</th></tr></thead>
          <tbody>{points.map((point) => <tr key={point.customer_id} className={point.customer_id === selectedId ? "selected-row" : ""}><th scope="row"><button type="button" onClick={() => onSelect(point.customer_id)} aria-pressed={point.customer_id === selectedId}>{point.customer_id}</button></th><td>{point.cluster}</td><td>{formatNumber(point[xFeature], 2)}</td><td>{formatNumber(point[yFeature], 2)}</td><td>{point.uncertainty_label}</td><td>{formatNumber(point.assignment_margin, 3)}</td></tr>)}</tbody>
        </table>
      </div>
    </details>
  );
}
