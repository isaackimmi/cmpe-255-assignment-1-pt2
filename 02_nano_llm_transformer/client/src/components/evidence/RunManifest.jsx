import { compactHash } from "../../utils/format";
import { Panel } from "../ui";

export function RunManifest({ metrics }) {
  const rows = [
    ["Seed", metrics?.seed],
    ["Context order", metrics?.behavior?.order ?? metrics?.config?.order],
    ["Vocabulary", metrics?.vocab_size ?? metrics?.vocabulary?.length],
    ["Device", metrics?.device],
    ["Corpus hash", compactHash(metrics?.corpus_sha256)],
  ];
  return (
    <Panel className="manifest-panel">
      <p className="kicker">RUN MANIFEST</p>
      <h2>Reproducible by design.</h2>
      <dl>{rows.map(([label, value]) => <div className="manifest-row" key={label}><dt>{label}</dt><dd>{value ?? "—"}</dd></div>)}</dl>
    </Panel>
  );
}
