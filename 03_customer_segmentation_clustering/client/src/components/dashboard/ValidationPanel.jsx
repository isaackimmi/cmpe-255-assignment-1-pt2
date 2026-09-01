import { Card, Chip } from "@mui/material";
import { formatNumber } from "../../utils/format";
import { SectionHeading } from "../common/SectionHeading";

export function ValidationPanel({ rows, selectedK, preprocessing }) {
  const visible = rows.filter((row) => row.preprocessing === preprocessing);
  return <Card component="article" className="panel"><SectionHeading eyebrow="VALIDATION" title="Does the shape hold?" action={<Chip label="12 repeated holdouts" size="small" variant="outlined" />} /><div className="scores">{visible.map((row) => <div className={`score-row ${Number(row.k) === Number(selectedK) ? "selected" : ""}`} key={row.k}><b>k={row.k}</b><span><i style={{ width: `${Math.max(3, Number(row.silhouette_mean) * 100)}%` }} /></span><strong>{formatNumber(row.silhouette_mean, 3)}</strong><small>ARI {formatNumber(row.stability_ari_mean, 3)}</small></div>)}</div><p className="note">Silhouette is an internal geometric signal; it is not campaign lift or proof of real customer personas.</p></Card>;
}
