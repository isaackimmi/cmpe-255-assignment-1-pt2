import { AppFooter } from "./AppFooter";
import { AppHeader } from "./AppHeader";

export function AppShell({ status, source, children }) {
  return (
    <>
      <AppHeader status={status} />
      <main>{children}</main>
      <AppFooter source={source} />
    </>
  );
}
