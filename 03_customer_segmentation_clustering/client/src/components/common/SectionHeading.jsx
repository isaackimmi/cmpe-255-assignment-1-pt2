export function SectionHeading({ eyebrow, title, description, action }) {
  return (
    <div className="panel-head">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {description && <p className="subtle">{description}</p>}
      </div>
      {action}
    </div>
  );
}
