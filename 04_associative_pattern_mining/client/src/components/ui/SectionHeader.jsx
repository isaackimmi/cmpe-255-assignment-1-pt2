export function SectionHeader({ eyebrow, title, note, action, compact = false }) {
  return (
    <div className={`section-head${compact ? " compact" : ""}`}>
      <div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>
      {action || (note && <p className="section-note">{note}</p>)}
    </div>
  );
}
