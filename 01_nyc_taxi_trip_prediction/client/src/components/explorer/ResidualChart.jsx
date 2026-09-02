/** @param {{rows: import('../../services/api').PredictionRow[]}} props */
export function ResidualChart({ rows = [] }) {
  const visible = rows.slice(0, 48);
  const absolute = visible.map((row) => Math.abs(Number(row.residual_seconds)));
  const mean = absolute.length
    ? absolute.reduce((sum, value) => sum + value, 0) / absolute.length
    : 0;
  const max = absolute.length ? Math.max(...absolute) : 0;
  const summary = `${visible.length} residuals shown. Mean absolute residual ${mean.toFixed(1)} seconds; maximum ${max.toFixed(1)} seconds.`;
  return (
    <figure className="residual-figure">
      <svg
        className="residuals"
        viewBox="0 0 480 120"
        role="img"
        aria-labelledby="residual-title"
        aria-describedby="residual-description"
        preserveAspectRatio="none"
      >
        <title id="residual-title">Absolute residual magnitude chart</title>
        <desc id="residual-description">{summary}</desc>
        <line x1="0" y1="118" x2="480" y2="118" className="residual-axis" />
        {visible.map((row, index) => {
          const height = Math.min(
            108,
            Math.max(6, Math.abs(Number(row.residual_seconds)) / 3),
          );
          return (
            <rect
              key={`${row.pickup_datetime}-${index}`}
              x={index * 10 + 1}
              y={118 - height}
              width="7"
              height={height}
            >
              <title>
                {row.pickup_datetime}: residual{" "}
                {Number(row.residual_seconds).toFixed(1)} seconds
              </title>
            </rect>
          );
        })}
      </svg>
      <figcaption>{summary}</figcaption>
    </figure>
  );
}
