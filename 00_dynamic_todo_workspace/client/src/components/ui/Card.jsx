export function Card({ as: Component = "article", className = "", children, ...props }) {
  return <Component className={`card ${className}`.trim()} {...props}>{children}</Component>;
}
