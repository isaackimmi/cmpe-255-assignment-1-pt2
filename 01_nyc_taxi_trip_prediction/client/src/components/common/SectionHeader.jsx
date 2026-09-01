export function SectionHeader({ eyebrow, title, description, light = false }) {
  return (
    <div className={`section-head${light ? " light" : ""}`}>
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      <p>{description}</p>
    </div>
  );
}
