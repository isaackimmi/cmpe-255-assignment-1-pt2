import LinearProgress from "@mui/material/LinearProgress";
import { Panel, PanelHeader } from "../common/Panel";
import { percent } from "../../utils/format";

export function ClassificationPanel({ metrics }) {
  const classification = metrics.classification;
  const scoreRows = [["Precision", classification.precision], ["Recall", classification.recall], ["Specificity", classification.specificity], ["F1", classification.f1]];
  return <div className="detail-grid"><Panel large><PanelHeader tag="FIXED DOMAIN RULE" value={`usage ≥ ${classification.threshold}`}/><table className="confusion-table"><caption>Classification confusion matrix</caption><thead><tr><th scope="col">Predicted \ Actual</th><th scope="col">Not renewed</th><th scope="col">Renewed</th></tr></thead><tbody><tr><th scope="row">Not renewed</th><td>{classification.confusion_matrix[0][0]}</td><td>{classification.confusion_matrix[0][1]}</td></tr><tr><th scope="row">Renewed</th><td>{classification.confusion_matrix[1][0]}</td><td>{classification.confusion_matrix[1][1]}</td></tr></tbody></table><p className="callout">{classification.rule} · {classification.threshold_source}</p></Panel><Panel><span className="tag">HOLDOUT METRICS</span><h3>{percent(classification.balanced_accuracy)} balanced accuracy</h3>{scoreRows.map(([name, value]) => <div className="bar-row" key={name}><span>{name}</span><LinearProgress aria-label={`${name}: ${percent(value)}`} variant="determinate" value={Number(value) * 100}/><b>{percent(value)}</b></div>)}<p className="muted">Majority baseline accuracy: {percent(classification.majority_baseline_accuracy)}</p></Panel></div>;
}
