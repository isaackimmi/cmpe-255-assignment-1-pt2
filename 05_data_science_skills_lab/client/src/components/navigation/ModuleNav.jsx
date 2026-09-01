import Button from "@mui/material/Button";
import { MODULES } from "../../constants/modules";

export function ModuleNav({ activeModule, onSelect }) {
  return <nav aria-label="Lab modules">
    {MODULES.map((item) => <Button key={item.id} className={`nav-button${activeModule === item.id ? " active" : ""}`} onClick={() => onSelect(item.id)} aria-current={activeModule === item.id ? "page" : undefined}>
      {item.index ? `${item.index} · ` : ""}{item.label}{item.id === "overview" && <span>↗</span>}
    </Button>)}
  </nav>;
}
