import { OverviewPanel } from "./OverviewPanel";
import { CleaningPanel } from "./CleaningPanel";
import { ClassificationPanel } from "./ClassificationPanel";
import { RegressionPanel } from "./RegressionPanel";
import { ClusteringPanel } from "./ClusteringPanel";

const registry = {
  overview: { Component: OverviewPanel, select: ({ metrics }) => ({ metrics }) },
  cleaning: { Component: CleaningPanel, select: ({ metrics }) => ({ metrics }) },
  classification: { Component: ClassificationPanel, select: ({ metrics }) => ({ metrics }) },
  regression: { Component: RegressionPanel, select: ({ metrics, moduleData, summary }) => ({ metrics, moduleData, fallbackPredictions: summary.summary.regression_predictions }) },
  clustering: { Component: ClusteringPanel, select: ({ metrics, rowsResult }) => ({ metrics, rows: rowsResult.rows, totalRows: metrics.data_quality.clean_rows }) },
};

/**
 * Selects the narrow contract needed by the active evidence panel.
 * @param {{module: string, metrics: object, moduleData: object|null, summary: object, rowsResult: {rows: Array<object>}}} props
 */
export function ModulePanel(props) {
  const entry = registry[props.module] || registry.overview;
  return <entry.Component {...entry.select(props)}/>;
}
