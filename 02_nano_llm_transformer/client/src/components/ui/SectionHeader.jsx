import { Badge } from "@radix-ui/themes";

/** @param {{eyebrow: string, title: string, description?: string, endpoint?: string}} props */
export function SectionHeader({ eyebrow, title, description, endpoint }) {
  return (
    <div className="section-head">
      <div>
        <p className="kicker">{eyebrow}</p>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {endpoint && <Badge className="api-badge">{endpoint}</Badge>}
    </div>
  );
}
