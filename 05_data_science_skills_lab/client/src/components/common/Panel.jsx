export function Panel({ children, large = false, className = "" }) {
  return <article className={`panel${large ? " large" : ""} ${className}`.trim()}>{children}</article>;
}

export function PanelHeader({ tag, value }) {
  return <div className="panel-top"><span className="tag">{tag}</span><strong>{value}</strong></div>;
}
