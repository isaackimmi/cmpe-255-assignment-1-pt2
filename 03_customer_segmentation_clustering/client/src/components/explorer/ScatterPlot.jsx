import { useRef } from "react";
import { FEATURES } from "../../constants/features";

function domain(rows, key) {
  const values = rows.map((point) => Number(point[key]));
  const min = Math.min(...values); const max = Math.max(...values); const spread = Math.max(max - min, 1);
  return [min - spread * 0.08, max + spread * 0.08];
}

export function ScatterPlot({ points, projection, xFeature, yFeature, selectedId, onSelect }) {
  const pointRefs = useRef(new Map());
  if (!points.length) return <div className="plot"><p className="empty">No points match this segment.</p></div>;
  const x = projection === "pca" ? "pca_x" : xFeature; const y = projection === "pca" ? "pca_y" : yFeature;
  const width = 760; const height = 420; const pad = 52; const xd = domain(points, x); const yd = domain(points, y);
  const sx = (value) => pad + (Number(value) - xd[0]) / (xd[1] - xd[0]) * (width - pad - 22);
  const sy = (value) => height - pad - (Number(value) - yd[0]) / (yd[1] - yd[0]) * (height - pad - 22);
  const activate = (event, index) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(points[index].customer_id); return; }
    const direction = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key];
    if (!direction) return;
    event.preventDefault();
    const next = (index + direction + points.length) % points.length;
    onSelect(points[next].customer_id);
    pointRefs.current.get(points[next].customer_id)?.focus();
  };
  return <div className="plot"><p id="plot-instructions" className="sr-only">Customer points. Use arrow keys to move between points and Enter or Space to select.</p><svg viewBox={`0 0 ${width} ${height}`} role="listbox" aria-label="Interactive customer segmentation scatter plot" aria-describedby="plot-instructions"><line className="axis" x1={pad} y1={height-pad} x2={width-22} y2={height-pad} /><line className="axis" x1={pad} y1={pad} x2={pad} y2={height-pad} /><text x={width/2} y={height-12} className="axis-label">{projection === "pca" ? "PC1" : FEATURES[x]}</text><text x="14" y={height/2} className="axis-label" transform={`rotate(-90 14 ${height/2})`}>{projection === "pca" ? "PC2" : FEATURES[y]}</text>{points.map((point, index) => <circle key={point.customer_id} ref={(node) => { if (node) pointRefs.current.set(point.customer_id, node); else pointRefs.current.delete(point.customer_id); }} cx={sx(point[x])} cy={sy(point[y])} r={point.customer_id === selectedId ? 8 : 5} className={`point cluster-${point.cluster} ${point.customer_id === selectedId ? "selected" : ""}`} tabIndex={point.customer_id === selectedId ? 0 : -1} role="option" aria-selected={point.customer_id === selectedId} aria-label={`${point.customer_id}, segment ${point.cluster}, ${point.uncertainty_label} assignment, margin ${point.assignment_margin}`} onClick={() => onSelect(point.customer_id)} onKeyDown={(event) => activate(event, index)} />)}</svg></div>;
}
