export function AppFooter({ source }) {
  return (
    <footer>
      PROJECT 01 · NYC TAXI TRIP DURATION{" "}
      <span>source · {source || "checked-in artifacts"}</span>
    </footer>
  );
}
