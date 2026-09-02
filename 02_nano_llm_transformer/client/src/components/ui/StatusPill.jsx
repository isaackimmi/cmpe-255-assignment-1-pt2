import { Badge } from "@radix-ui/themes";

export function StatusPill({ children, tone = "lime", className = "" }) {
  return <Badge className={className} color={tone}>{children}</Badge>;
}
