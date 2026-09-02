const MANIFESTS = {
  success: { label: "Verified success run", path: "../artifacts/run_manifest.json" },
  failure: { label: "Verified failure run", path: "../artifacts/run_manifest_failure.json" },
};

const graphCanvas = document.querySelector("#graph-canvas");
const edgeLayer = document.querySelector("#edge-layer");
const timeline = document.querySelector("#timeline");
const runButton = document.querySelector("#hero-run");
const resetButton = document.querySelector("#reset-demo");
const manifestSelect = document.querySelector("#manifest-select");
const graphStatus = document.querySelector("#graph-status");
const timelineTitle = document.querySelector("#timeline-title");
const timelineCount = document.querySelector("#timeline-count");
const runResult = document.querySelector("#run-result");
const selectedOutput = document.querySelector("#inspector-output");
const nodes = [];

let manifest = null;
let taskNames = [];
let selectedTask = null;
let viewStatuses = {};
let replaying = false;
let replayToken = 0;

function statusLabel(status) {
  return { pending: "Waiting", running: "Running…", succeeded: "Succeeded", failed: "Failed", skipped: "Skipped" }[status] || status;
}

function statusClass(status) {
  return { pending: "waiting", running: "running", succeeded: "complete", failed: "failed", skipped: "skipped" }[status] || "waiting";
}

function terminal(status) { return ["succeeded", "failed", "skipped"].includes(status); }
function short(value, length = 18) { return !value ? "—" : value.length > length ? `${value.slice(0, length)}…` : value; }
function taskRecord(name) { return manifest?.tasks?.[name] || {}; }
function outputRecord(name) { return taskRecord(name).output || null; }

function buildManifestPicker() {
  if (!manifestSelect) return;
  manifestSelect.innerHTML = Object.entries(MANIFESTS).map(([key, item]) => `<option value="${key}">${item.label}</option>`).join("");
}

function buildNodes() {
  graphCanvas.querySelectorAll(".task-node").forEach((node) => node.remove());
  nodes.length = 0;
  taskNames.forEach((name, index) => {
    const record = taskRecord(name);
    const node = document.createElement("button");
    node.type = "button";
    node.className = `task-node node-position-${index}`;
    node.dataset.task = name;
    node.setAttribute("aria-label", `Inspect ${name} task`);
    node.innerHTML = `<span class="node-index">${String(index + 1).padStart(2, "0")}</span>
      <span class="node-icon">${index === 0 ? "↳" : index === taskNames.length - 1 ? "↗" : "⌁"}</span>
      <span class="node-name">${name}</span>
      <span class="node-kind">${record.depends_on?.length ? "TASK" : "SOURCE"}</span>
      <span class="node-status" data-status></span>`;
    node.addEventListener("click", () => { selectedTask = name; render(); });
    graphCanvas.appendChild(node);
    nodes.push(node);
  });
  positionNodes();
}

function positionNodes() {
  const compact = window.matchMedia("(max-width: 680px)").matches;
  graphCanvas.style.minHeight = compact ? `${Math.max(315, taskNames.length * 160 + 40)}px` : "315px";
  nodes.forEach((node, index) => {
    node.style.left = compact ? "50%" : `${taskNames.length === 1 ? 50 : 8 + (index * 84) / (taskNames.length - 1)}%`;
    node.style.top = compact ? `${22 + index * 160}px` : "79px";
    node.style.transform = "translateX(-50%)";
  });
}

function renderTimeline() {
  const terminalCount = taskNames.filter((name) => terminal(viewStatuses[name])).length;
  timeline.innerHTML = taskNames.map((name, index) => {
    const status = viewStatuses[name] || "pending";
    return `<div class="timeline-step ${statusClass(status)}" data-timeline-task="${name}">
      <span class="timeline-dot">${status === "succeeded" ? "✓" : status === "failed" ? "!" : String(index + 1).padStart(2, "0")}</span>
      <span class="timeline-name">${name}</span>
    </div>`;
  }).join("");
  timelineCount.textContent = `${terminalCount} / ${taskNames.length} terminal`;
}

function setDetail(id, value) { const element = document.querySelector(`#${id}`); if (element) element.textContent = value || "—"; }

function renderInspector() {
  if (!manifest || !selectedTask) return;
  const record = taskRecord(selectedTask);
  const output = outputRecord(selectedTask);
  const status = viewStatuses[selectedTask] || "pending";
  const index = taskNames.indexOf(selectedTask);
  setDetail("inspector-title", selectedTask);
  setDetail("inspector-number", String(index + 1).padStart(2, "0"));
  setDetail("inspector-description", record.config ? `Recorded task configuration: ${JSON.stringify(record.config)}` : "Task recorded by the FlowForge runner.");
  setDetail("inspector-type", record.depends_on?.length ? "task" : "source");
  setDetail("inspector-deps", record.depends_on?.join(", ") || "—");
  setDetail("inspector-produces", output?.schema_fingerprint ? "artifact" : "pending");
  setDetail("inspector-status", statusLabel(status));
  setDetail("inspector-run", short(output?.run_id || manifest.run_id, 22));
  setDetail("inspector-seed", manifest.seed === null || manifest.seed === undefined ? "—" : String(manifest.seed));
  setDetail("inspector-started", short(manifest.started_at, 22));
  setDetail("inspector-artifact", short(output?.artifact_id, 22));
  setDetail("inspector-parents", output?.parent_artifact_ids?.map((id) => short(id, 10)).join(", ") || "—");
  setDetail("inspector-content", short(output?.content_hash, 22));
  setDetail("inspector-schema", short(output?.schema_fingerprint, 22));
  setDetail("inspector-code", short(record.code_fingerprint, 22));
  setDetail("inspector-config", short(record.config_fingerprint, 22));
  selectedOutput.textContent = output && status === "succeeded" ? output.preview : status === "failed" ? (record.error?.message || "task failed") : "artifact not available in this replay step";
  const outputState = document.querySelector("#output-state");
  outputState.textContent = statusLabel(status).toLowerCase();
  outputState.className = `output-state ${statusClass(status)}`;
  setDetail("inspector-step", `Task ${index + 1} of ${taskNames.length}`);
  nodes.forEach((node) => node.classList.toggle("selected", node.dataset.task === selectedTask));
}

function renderNodes() {
  nodes.forEach((node) => {
    const status = viewStatuses[node.dataset.task] || "pending";
    node.classList.remove("status-complete", "status-running", "status-waiting", "status-failed", "status-skipped");
    node.classList.add(`status-${statusClass(status)}`);
    node.querySelector("[data-status]").textContent = statusLabel(status);
  });
}

function drawEdges() {
  if (!manifest || !graphCanvas || !edgeLayer) return;
  const bounds = graphCanvas.getBoundingClientRect();
  edgeLayer.setAttribute("viewBox", `0 0 ${bounds.width} ${bounds.height}`);
  edgeLayer.innerHTML = `<defs><marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z"></path></marker></defs>`;
  taskNames.forEach((name) => {
    const target = graphCanvas.querySelector(`[data-task="${name}"]`);
    (taskRecord(name).depends_on || []).forEach((dependency) => {
      const source = graphCanvas.querySelector(`[data-task="${dependency}"]`);
      if (!source || !target) return;
      const from = source.getBoundingClientRect();
      const to = target.getBoundingClientRect();
      const horizontal = Math.abs(from.top - to.top) < 40;
      const x1 = from.left - bounds.left + (horizontal ? from.width : from.width / 2);
      const y1 = from.top - bounds.top + (horizontal ? from.height / 2 : from.height);
      const x2 = to.left - bounds.left + (horizontal ? 0 : to.width / 2);
      const y2 = to.top - bounds.top + (horizontal ? to.height / 2 : 0);
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", x1); line.setAttribute("y1", y1); line.setAttribute("x2", x2); line.setAttribute("y2", y2);
      line.classList.toggle("active", viewStatuses[dependency] === "succeeded");
      edgeLayer.appendChild(line);
    });
  });
}

function renderCopy() {
  if (!manifest) return;
  const finalStatus = manifest.status;
  const terminalCount = taskNames.filter((name) => terminal(viewStatuses[name])).length;
  graphStatus.innerHTML = `<b></b> ${replaying ? "Replaying recorded run" : `Verified · ${finalStatus}`}`;
  graphStatus.classList.toggle("done", !replaying && finalStatus === "succeeded");
  timelineTitle.textContent = replaying ? "Replaying recorded task states" : `${finalStatus === "succeeded" ? "Verified run complete" : "Verified failure state"}`;
  if (replaying) {
    runResult.innerHTML = '<span class="result-icon">◌</span><span><strong>Recorded manifest replay.</strong> The browser is revealing states captured by the Python runner.</span>';
  } else if (finalStatus === "failed") {
    runResult.innerHTML = `<span class="result-icon">!</span><span><strong>Fail-fast run.</strong> ${manifest.error?.message || "A task failed; downstream tasks were skipped."}</span>`;
  } else {
    runResult.innerHTML = `<span class="result-icon">✦</span><span><strong>Verified run loaded.</strong> ${terminalCount} task states and artifact envelopes came from the checked-in Python manifest.</span>`;
  }
  runButton.innerHTML = `<span class="button-icon" aria-hidden="true">${replaying ? "◌" : "↻"}</span> ${replaying ? "Replaying…" : "Replay recorded run"}`;
  runButton.classList.toggle("running", replaying);
}

function render() { renderNodes(); renderTimeline(); renderInspector(); drawEdges(); renderCopy(); }

async function replayManifest() {
  if (!manifest || replaying) return;
  const token = ++replayToken;
  replaying = true;
  viewStatuses = Object.fromEntries(taskNames.map((name) => [name, "pending"]));
  render();
  for (const name of taskNames) {
    const status = taskRecord(name).status;
    if (status === "pending") continue;
    await new Promise((resolve) => window.setTimeout(resolve, 520));
    if (token !== replayToken) return;
    viewStatuses[name] = status;
    render();
  }
  replaying = false;
  render();
}

function resetReplay() {
  replayToken += 1;
  replaying = false;
  viewStatuses = Object.fromEntries(taskNames.map((name) => [name, taskRecord(name).status]));
  render();
}

async function loadManifest(key = "success") {
  replayToken += 1;
  replaying = false;
  try {
    const response = await fetch(MANIFESTS[key].path, { cache: "no-store" });
    if (!response.ok) throw new Error(`manifest request failed (${response.status})`);
    manifest = await response.json();
    taskNames = manifest.task_order || Object.keys(manifest.tasks || {});
    selectedTask = taskNames[0] || null;
    viewStatuses = Object.fromEntries(taskNames.map((name) => [name, taskRecord(name).status]));
    buildNodes();
    render();
  } catch (error) {
    graphStatus.innerHTML = `<b></b> Manifest unavailable`;
    runResult.innerHTML = `<span class="result-icon">!</span><span><strong>Start the local static server.</strong> ${error.message}</span>`;
  }
}

buildManifestPicker();
manifestSelect?.addEventListener("change", (event) => loadManifest(event.target.value));
runButton?.addEventListener("click", replayManifest);
resetButton?.addEventListener("click", resetReplay);
window.addEventListener("resize", () => { positionNodes(); drawEdges(); });
window.addEventListener("load", drawEdges);
loadManifest("success");
