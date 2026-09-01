import { Card } from "@mui/material";

const STEPS = [["01", "Understand", "120 generated customers, 4 numeric features."], ["02", "Prepare", "Validate domains; fit StandardScaler on each training split."], ["03", "Model", "Compare K-Means candidates k=2…7 with 25 starts."], ["04", "Evaluate", "Held-out silhouette, ARI stability, and descriptive diagnostics."]];

export function MethodPanel() {
  return <Card component="article" className="panel method"><p className="eyebrow">CRISP-DM TRACE</p><h2>From data contract to segment hypothesis.</h2><div className="steps">{STEPS.map(([number, title, note]) => <div key={number}><b>{number}</b><strong>{title}</strong><span>{note}</span></div>)}</div></Card>;
}
