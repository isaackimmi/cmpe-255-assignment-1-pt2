import { Chip } from "@mui/material";

export function AppHeader({ status }) {
  const online = status === "success";
  return (
    <header className="topbar">
      <a className="brand" href="#top" aria-label="Taxi Lab home">
        <span className="mark">01</span>
        <span>
          <b>TAXI LAB</b>
          <small>NYC TRIP DURATION</small>
        </span>
      </a>
      <nav aria-label="Primary navigation">
        <a href="#evidence">Evidence</a>
        <a href="#explorer">Explorer</a>
        <a href="#estimate">Estimator</a>
      </nav>
      <Chip
        className="status"
        size="small"
        color={online ? "success" : status === "error" ? "error" : "default"}
        label={
          online
            ? "API ONLINE"
            : status === "error"
              ? "API UNAVAILABLE"
              : "CONNECTING"
        }
      />
    </header>
  );
}
