import { Paper } from "@mui/material";
import { durationClock } from "../../utils/format";

export function EstimateResult({ result }) {
  return (
    <Paper
      component="article"
      className="estimate-result panel"
      elevation={0}
      aria-live="polite"
    >
      <span className="eyebrow">API RESPONSE</span>
      <strong>
        {result ? durationClock(result.estimated_duration_seconds) : "—:—"}
      </strong>
      <p>
        {result?.disclaimer ||
          "Submit a valid route to see the server response."}
      </p>
      <div className="mini-stat">
        <span>distance</span>
        <b>{result ? `${result.distance_miles} mi` : "—"}</b>
        <span>context</span>
        <b>{result ? (result.is_rush_hour ? "rush hour" : "off-peak") : "—"}</b>
      </div>
      <small>
        Deterministic synthetic teaching estimate · no production claim
      </small>
    </Paper>
  );
}
