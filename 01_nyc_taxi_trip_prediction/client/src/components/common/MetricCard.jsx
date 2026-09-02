import { Card, CardContent, Typography } from "@mui/material";

/** @param {{label: string, value: string|number, caption: string, accent?: boolean}} props */
export function MetricCard({ label, value, caption, accent = false }) {
  return (
    <Card
      className={`metric${accent ? " accent" : ""}`}
      elevation={0}
      square
      role="listitem"
    >
      <CardContent sx={{ p: 0, "&:last-child": { pb: 0 } }}>
        <Typography component="small">{label}</Typography>
        <Typography component="strong">{value}</Typography>
        <Typography component="span">{caption}</Typography>
      </CardContent>
    </Card>
  );
}
