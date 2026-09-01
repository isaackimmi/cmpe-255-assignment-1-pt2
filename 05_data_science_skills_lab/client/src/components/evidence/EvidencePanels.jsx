import { EvidenceErrorBoundary } from "./EvidenceErrorBoundary";
import { ModulePanel } from "../modules/ModulePanel";

export function EvidencePanels(props) {
  return <EvidenceErrorBoundary resetKey={props.module}><ModulePanel {...props}/></EvidenceErrorBoundary>;
}
