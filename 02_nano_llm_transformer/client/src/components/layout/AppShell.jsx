import { Button, Callout } from "@radix-ui/themes";
import { TopBar } from "./TopBar";
import { SiteFooter } from "./SiteFooter";

export function AppShell({ status, loadError, onRetry, children }) {
  return (
    <>
      <TopBar status={status} />
      {status === "connecting" && <p className="evidence-loading" role="status" aria-live="polite">Loading model evidence…</p>}
      {loadError && (
        <Callout.Root className="evidence-error" color={status === "partial" ? "orange" : "red"} role="alert">
          <Callout.Text>{loadError}</Callout.Text>
          <Button className="retry-evidence" variant="soft" onClick={onRetry}>Retry evidence</Button>
        </Callout.Root>
      )}
      <main className="app-main" id="top">{children}</main>
      <SiteFooter />
    </>
  );
}
