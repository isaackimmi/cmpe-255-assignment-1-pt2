export function TemporalSplit({ metrics }) {
  const split = metrics.split_cutoff || {};
  return (
    <div className="split-card">
      <strong>
        {Number(metrics.train_rows).toLocaleString()} /{" "}
        {Number(metrics.test_rows).toLocaleString()}
      </strong>
      <span>train / holdout rows</span>
      <code>
        {split.train_max_pickup_datetime}
        <br />→ {split.test_min_pickup_datetime}
      </code>
      <small>Strict forward invariant: train max &lt; test min</small>
    </div>
  );
}
