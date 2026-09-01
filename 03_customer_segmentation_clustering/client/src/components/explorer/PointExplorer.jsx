import { useEffect } from "react";
import { Card } from "@mui/material";
import { FEATURES, FEATURE_KEYS } from "../../constants/features";
import { SelectField } from "../common/SelectField";
import { SectionHeading } from "../common/SectionHeading";
import { PointInspector } from "./PointInspector";
import { ScatterPlot } from "./ScatterPlot";
import { ExplorerDataTable } from "./ExplorerDataTable";

export function PointExplorer({ points, profiles, cluster, onClusterChange, projection, onProjectionChange, xFeature, onXChange, yFeature, onYChange, selectedId, onSelect }) {
  const visible = points.filter((point) => cluster === "all" || String(point.cluster) === cluster);
  const selected = visible.find((point) => point.customer_id === selectedId) || null;
  useEffect(() => {
    if (visible.length && !visible.some((point) => point.customer_id === selectedId)) onSelect(visible[0].customer_id);
  }, [visible, selectedId, onSelect]);
  const featureOptions = FEATURE_KEYS.map((key) => ({ value: key, label: FEATURES[key] }));
  const toolbar = <div className="toolbar"><SelectField id="cluster-filter" label="Segment" value={cluster} onChange={(event) => onClusterChange(event.target.value)} options={[{ value: "all", label: "All segments" }, ...profiles.map((profile) => ({ value: String(profile.cluster), label: `Segment ${profile.cluster}` }))]} /><SelectField id="projection" label="Projection" value={projection} onChange={(event) => onProjectionChange(event.target.value)} options={[{ value: "raw", label: "Raw feature pair" }, { value: "pca", label: "PCA visualization" }]} /><SelectField id="x-feature" label="X axis" value={xFeature} onChange={(event) => onXChange(event.target.value)} options={featureOptions} disabled={projection === "pca"} /><SelectField id="y-feature" label="Y axis" value={yFeature} onChange={(event) => onYChange(event.target.value)} options={featureOptions} disabled={projection === "pca"} /></div>;
  return <Card component="section" className="panel explorer"><SectionHeading eyebrow="POINT EXPLORER" title="Inspect customers, not just averages." description={<>Every point is returned by FastAPI from <code>explorer_points.csv</code>. Use arrow keys within the plot or open the accessible data table.</>} action={toolbar} /><div className="explorer-body"><ScatterPlot points={visible} projection={projection} xFeature={xFeature} yFeature={yFeature} selectedId={selected?.customer_id} onSelect={onSelect} /><PointInspector point={selected} /></div><ExplorerDataTable points={visible} selectedId={selected?.customer_id} onSelect={onSelect} xFeature={xFeature} yFeature={yFeature} /><p className="note">PCA is visualization-only. Distance, margin, and confidence are geometry diagnostics in fitted scaled space—not probabilities or outcome predictions.</p></Card>;
}
