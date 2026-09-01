import { Card } from "@radix-ui/themes";

/** Reusable Radix-backed surface. @param {{as?: React.ElementType, className?: string, children: React.ReactNode}} props */
export function Panel({ as: Element = "article", className = "", children, ...props }) {
  return (
    <Card asChild>
      <Element className={`panel ${className}`.trim()} {...props}>{children}</Element>
    </Card>
  );
}
