/** @param {{rows: import('../../services/api').FeatureImportanceRow[]}} props */
export function FeatureImportance({ rows = [] }) {
  const visible = rows.slice(0, 6);
  const max = Math.max(
    ...visible.map((row) => Number(row.absolute_coefficient) || 0),
    1,
  );
  return (
    <ol
      className="importance"
      aria-label="Top standardized feature coefficients"
    >
      {visible.map((row) => {
        const coefficient = Number(row.absolute_coefficient);
        return (
          <li className="bar-row" key={row.feature}>
            <span>{row.feature}</span>
            <span className="importance-track" aria-hidden="true">
              <span
                style={{ width: `${Math.max(4, (coefficient / max) * 100)}%` }}
              />
            </span>
            <strong>
              <span className="sr-only">absolute coefficient </span>
              {coefficient.toFixed(2)}
            </strong>
          </li>
        );
      })}
    </ol>
  );
}
