import { AppHeader } from "./AppHeader";

export function AppShell({ status, children }) {
  return (
    <main className="shell">
      <AppHeader status={status} />
      {children}
      <footer>
        CMPE 255 · Project 03 · synthetic teaching sample · <a href="../README.md">README</a>
      </footer>
    </main>
  );
}
