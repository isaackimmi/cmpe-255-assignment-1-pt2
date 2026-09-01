import { Chip, Paper } from "@mui/material";
import { seconds } from "../../utils/format";
import { PredictionTable } from "./PredictionTable";
import { ResidualChart } from "./ResidualChart";

/** @param {{result: import('../../services/api').PredictionSliceResponse}} props */
export function SliceResults({ result }) {
  const model = result.metrics || {};
  const baseline = model.baseline || {};
  return (
    <div className="slice-layout">
      <Paper component="article" className="panel slice-card" elevation={0}>
        <div className="panel-head">
          <div>
            <span className="eyebrow">server-computed slice</span>
            <h3>
              {result.slice} · {result.population}
            </h3>
          </div>
          <Chip
            size="small"
            label={`${Number(model.rows).toLocaleString()} rows`}
          />
        </div>
        <div className="compare">
          <div>
            <small>MODEL MAE</small>
            <strong>{seconds(model.mae_seconds)}</strong>
          </div>
          <div>
            <small>BASELINE MAE</small>
            <strong>{seconds(baseline.mae_seconds)}</strong>
          </div>
          <div>
            <small>R²</small>
            <strong>
              {model.r2 == null ? "—" : Number(model.r2).toFixed(3)}
            </strong>
          </div>
        </div>
        <ResidualChart rows={result.rows} />
        <p className="note">
          Distance boundary: {Number(result.distance_boundary_miles).toFixed(2)}{" "}
          mi. Bars show absolute residual magnitude for the first 48 returned
          rows; hover for timestamp and signed residual.
        </p>
      </Paper>
      <Paper component="article" className="panel" elevation={0}>
        <div className="panel-head">
          <span className="eyebrow">row evidence</span>
          <Chip size="small" label="predictions.csv" />
        </div>
        <PredictionTable rows={result.rows} />
      </Paper>
    </div>
  );
}
