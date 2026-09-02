export function Button({ variant = "primary", className = "", children, ...props }) {
  return (
    <button className={`button ${variant} ${className}`.trim()} type="button" {...props}>
      {children}
    </button>
  );
}
