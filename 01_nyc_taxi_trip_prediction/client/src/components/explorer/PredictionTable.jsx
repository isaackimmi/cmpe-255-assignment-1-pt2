import { seconds } from "../../utils/format";

/** @param {{rows: import('../../services/api').PredictionRow[]}} props */
export function PredictionTable({ rows = [] }) {
  return (
    <div
      className="table-scroll"
      role="region"
      aria-label="Prediction evidence table"
      tabIndex="0"
    >
      <table className="prediction-table">
        <caption className="sr-only">
          Actual and predicted trip durations with signed residuals
        </caption>
        <thead>
          <tr>
            <th scope="col">Pickup</th>
            <th scope="col">Actual</th>
            <th scope="col">Prediction</th>
            <th scope="col">Residual</th>
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 8).map((row, index) => (
            <tr key={`${row.pickup_datetime}-${index}`}>
              <td>{row.pickup_datetime}</td>
              <td>{seconds(row.actual)}</td>
              <td>{seconds(row.prediction)}</td>
              <td
                className={
                  Number(row.residual_seconds) > 0 ? "positive" : "negative"
                }
              >
                {Number(row.residual_seconds).toFixed(1)}s
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
