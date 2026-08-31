const TASKS = [
  {
    name: "load_data",
    number: "01",
    type: "source",
    kind: "SOURCE",
    depends: "—",
    produces: "list[dict]",
    description: "Loads the raw observations that start this data-science workflow.",
    output: "[{age: 22, score: 81}, {age: null, score: 74}, …]",
  },
  {
    name: "clean_data",
    number: "02",
    type: "transform",
    kind: "TRANSFORM",
    depends: "load_data",
    produces: "list[dict]",
    description: "Fills missing values so downstream tasks receive a usable table.",
    output: "[{age: 22, score: 81}, {age: 0, score: 74}, …]",
  },
  {
    name: "summarize",
    number: "03",
    type: "analyze",
    kind: "ANALYZE",
    depends: "clean_data",
    produces: "dict",
    description: "Counts rows and calculates the cohort's mean score.",
    output: "{count: 3, mean_score: 83.333…}",
  },
  {
    name: "report",
    number: "04",
    type: "output",
    kind: "OUTPUT",
    depends: "summarize",
    produces: "str",
    description: "Turns the summary into a concise, human-readable result.",
    output: '"Processed 3 rows; mean score=83.3"',
  },
];

const taskByName = Object.fromEntries(TASKS.map((task) => [task.name, task]));
const nodes = [...document.querySelectorAll(".task-node")];
const timeline = document.querySelector("#timeline");
const edgeLayer = document.querySelector("#edge-layer");
const graphCanvas = document.querySelector("#graph-canvas");
const runButton = document.querySelector("#hero-run");
const resetButton = document.querySelector("#reset-demo");
const graphStatus = document.querySelector("#graph-status");
const timelineTitle = document.querySelector("#timeline-title");
const timelineCount = document.querySelector("#timeline-count");
const runResult = document.querySelector("#run-result");
const selectedOutput = document.querySelector("#inspector-output");
let selectedTask = "load_data";
let completed = [];
let running = false;
let runToken = 0;

function renderTimeline() {
  timeline.innerHTML = TASKS.map((task, index) => {
    const isComplete = completed.includes(task.name);
    const isActive = running && completed.length === index;
    const className = isComplete ? "complete" : isActive ? "active" : "";
    return `<div class="timeline-step ${className}" data-timeline-task="${task.name}">
      <span class="timeline-dot">${isComplete ? "✓" : task.number}</span><span class="timeline-name">${task.name}</span>
    </div>`;
  }).join("");
  timelineCount.textContent = `${completed.length} / ${TASKS.length} complete`;
}

function renderInspector(name = selectedTask) {
  const task = taskByName[name];
  selectedTask = name;
  nodes.forEach((node) => node.classList.toggle("selected", node.dataset.task === name));
  document.querySelector("#inspector-title").textContent = task.name;
  document.querySelector("#inspector-number").textContent = task.number;
  document.querySelector("#inspector-description").textContent = task.description;
  document.querySelector("#inspector-type").textContent = task.type;
  document.querySelector("#inspector-deps").textContent = task.depends;
  document.querySelector("#inspector-produces").textContent = task.produces;
  const isComplete = completed.includes(name);
  selectedOutput.textContent = isComplete ? task.output : "awaiting demo run";
  document.querySelector("#output-state").textContent = isComplete ? "complete" : "ready";
  document.querySelector("#output-state").classList.toggle("complete", isComplete);
  document.querySelector("#inspector-step").textContent = `Step ${task.number} of ${TASKS.length}`;
}

function renderNodes() {
  nodes.forEach((node) => {
    const name = node.dataset.task;
    const index = TASKS.findIndex((task) => task.name === name);
    const status = completed.includes(name) ? "complete" : running && completed.length === index ? "running" : "waiting";
    node.classList.remove("status-complete", "status-running", "status-waiting");
    node.classList.add(`status-${status}`);
    node.querySelector("[data-status]").textContent = status === "complete" ? "Complete" : status === "running" ? "Running…" : index === 0 ? "Ready" : "Waiting";
  });
}

function drawEdges() {
  if (!graphCanvas || !edgeLayer) return;
  const bounds = graphCanvas.getBoundingClientRect();
  edgeLayer.setAttribute("viewBox", `0 0 ${bounds.width} ${bounds.height}`);
  edgeLayer.innerHTML = `<defs><marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z"></path></marker></defs>`;
  TASKS.slice(0, -1).forEach((task, index) => {
    const from = graphCanvas.querySelector(`[data-task="${task.name}"]`).getBoundingClientRect();
    const to = graphCanvas.querySelector(`[data-task="${TASKS[index + 1].name}"]`).getBoundingClientRect();
    const horizontal = Math.abs(from.top - to.top) < 40;
    const x1 = from.left - bounds.left + (horizontal ? from.width : from.width / 2);
    const y1 = from.top - bounds.top + (horizontal ? from.height / 2 : from.height);
    const x2 = to.left - bounds.left + (horizontal ? 0 : to.width / 2);
    const y2 = to.top - bounds.top + (horizontal ? to.height / 2 : 0);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x1); line.setAttribute("y1", y1); line.setAttribute("x2", x2); line.setAttribute("y2", y2);
    line.classList.toggle("active", completed.includes(task.name));
    edgeLayer.appendChild(line);
  });
}

function render() { renderNodes(); renderTimeline(); renderInspector(selectedTask); drawEdges(); }

function setRunCopy() {
  if (completed.length === TASKS.length) {
    graphStatus.innerHTML = "<b></b> Demo complete";
    graphStatus.classList.add("done");
    timelineTitle.textContent = "All dependencies resolved";
    runResult.innerHTML = '<span class="result-icon">✦</span><span><strong>Run complete.</strong> Four tasks finished in stable topological order.</span>';
    runButton.innerHTML = '<span class="button-icon" aria-hidden="true">↻</span> Replay demo';
    runButton.classList.remove("running");
  } else if (running) {
    const current = TASKS[completed.length];
    graphStatus.innerHTML = `<b></b> Running ${current.name}`;
    graphStatus.classList.remove("done");
    timelineTitle.textContent = `Executing ${current.name}`;
    runResult.innerHTML = `<span class="result-icon">◌</span><span><strong>${current.name}</strong> is running after its dependencies succeeded.</span>`;
    runButton.innerHTML = '<span class="button-icon" aria-hidden="true">◌</span> Running…';
    runButton.classList.add("running");
  } else {
    graphStatus.innerHTML = "<b></b> Ready to run";
    graphStatus.classList.remove("done");
    timelineTitle.textContent = "The runner is ready";
    runResult.innerHTML = '<span class="result-icon">✦</span><span>Press <strong>Run demo</strong> to replay the same stable order the Python runner produces.</span>';
    runButton.innerHTML = '<span class="button-icon" aria-hidden="true">▶</span> Run demo';
    runButton.classList.remove("running");
  }
}

async function runDemo() {
  const token = ++runToken;
  if (running) return;
  if (completed.length === TASKS.length) completed = [];
  running = true;
  setRunCopy(); render();
  for (let i = completed.length; i < TASKS.length; i += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 720));
    if (token !== runToken) return;
    completed.push(TASKS[i].name);
    render(); setRunCopy();
  }
  running = false;
  render(); setRunCopy();
}

function resetDemo() { runToken += 1; running = false; completed = []; render(); setRunCopy(); }

nodes.forEach((node) => node.addEventListener("click", () => { renderInspector(node.dataset.task); drawEdges(); }));
runButton.addEventListener("click", runDemo);
resetButton.addEventListener("click", resetDemo);
window.addEventListener("resize", drawEdges);
window.addEventListener("load", drawEdges);
render(); setRunCopy();
