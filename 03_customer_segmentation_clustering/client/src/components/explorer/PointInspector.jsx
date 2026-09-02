import { FEATURES, FEATURE_KEYS } from "../../constants/features";
import { formatNumber } from "../../utils/format";

export function PointInspector({ point }) {
  if (!point) return <aside className="detail"><p className="empty">Select a point to inspect one synthetic customer.</p></aside>;
  return <aside className="detail" aria-live="polite"><p className="eyebrow">POINT INSPECTOR</p><h3>{point.customer_id} <span>Segment {point.cluster}</span></h3><div className={`pill ${point.uncertainty_label}`}>{point.uncertainty_label} assignment</div><p className="subtle">A synthetic record with a geometry-based diagnostic.</p><div className="detail-grid">{FEATURE_KEYS.map((key) => <div key={key}><span>{FEATURES[key]}</span><b>{formatNumber(point[key], key === "purchase_frequency" ? 2 : 1)}</b></div>)}</div><hr /><div className="detail-grid"><div><span>Distance</span><b>{formatNumber(point.centroid_distance, 3)}</b></div><div><span>Margin</span><b>{formatNumber(point.assignment_margin, 3)}</b></div><div><span>Confidence proxy</span><b>{formatNumber(point.assignment_confidence, 3)}</b></div></div></aside>;
}
