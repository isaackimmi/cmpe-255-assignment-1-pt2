import { Chip, Paper } from "@mui/material";
import { MetricCard } from "../common/MetricCard";
import { MetricGrid } from "../common/MetricGrid";
import { SectionHeader } from "../common/SectionHeader";
import { FeatureImportance } from "./FeatureImportance";
import { TemporalSplit } from "./TemporalSplit";
import { seconds } from "../../utils/format";
import "./evidence.css";

/** @param {{metrics: import('../../services/api').ExperimentResponse, importance: import('../../services/api').FeatureImportanceRow[]}} props */
export function EvidenceSection({ metrics, importance }) {
  const model = metrics.linear_log_target || {};
  const baseline = metrics.baseline || {};
  return (
    <section id="evidence" className="section evidence-section">
      <SectionHeader
        eyebrow="01 / evidence"
        title="The model earns its headline."
        description="Every number below is returned by FastAPI from checked-in experiment artifacts. The Python run remains the source of truth."
      />
      <MetricGrid ariaLabel="Holdout evaluation metrics">
        <MetricCard
          accent
          label="MODEL MAE"
          value={seconds(model.mae_seconds)}
          caption="average absolute error"
        />
        <MetricCard
          label="BASELINE MAE"
          value={seconds(baseline.mae_seconds)}
          caption="global median comparator"
        />
        <MetricCard
          label="MODEL R²"
          value={Number(model.r2).toFixed(3)}
          caption="variance explained"
        />
        <MetricCard
          label="HOLDOUT"
          value={Number(metrics.test_rows).toLocaleString()}
          caption="eligible future rows"
        />
      </MetricGrid>
      <div className="evidence-grid">
        <Paper component="article" className="panel" elevation={0}>
          <div className="panel-head">
            <span className="eyebrow">temporal split</span>
            <Chip size="small" label="forward-only" />
          </div>
          <TemporalSplit metrics={metrics} />
        </Paper>
        <Paper component="article" className="panel" elevation={0}>
          <div className="panel-head">
            <span className="eyebrow">model lens</span>
            <Chip size="small" label="coefficients" />
          </div>
          <FeatureImportance rows={importance} />
        </Paper>
      </div>
    </section>
  );
}
