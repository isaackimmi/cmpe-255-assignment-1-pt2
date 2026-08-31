const METHOD_LABELS = {
  isolation_forest: { label: "Isolation Forest", short: "IF", note: "Random partitions" },
  local_outlier_factor: { label: "Local Outlier Factor", short: "LOF", note: "Density contrast" },
  elliptic_envelope: { label: "Elliptic Envelope", short: "EE", note: "Robust covariance" },
  rank_ensemble: { label: "Rank ensemble", short: "ENSEMBLE", note: "Percentile blend" },
};
const CATEGORY_LABELS = { global: "Global", local: "Local", cluster: "Cluster" };
let metrics = null;
let selectedMethod = "elliptic_envelope";

const $ = (selector) => document.querySelector(selector);
const formatPct = (value) => `${Math.round(value * 100)}%`;
const formatScore = (value) => Number(value).toFixed(3);
const titleCase = (name) => METHOD_LABELS[name]?.label || name.replaceAll("_", " ");

function methodNames() {
  return Object.keys(metrics || {}).filter((name) => metrics[name] && typeof metrics[name].roc_auc === "number");
}

function renderSummary() {
  const names = methodNames();
  const best = names.reduce((winner, name) => metrics[name].roc_auc > metrics[winner].roc_auc ? name : winner, names[0]);
  const anomalyRate = metrics[best].flagged ? metrics[best].flagged / 900 : 0;
  $("#best-method").textContent = titleCase(best);
  $("#best-auc").textContent = formatScore(metrics[best].roc_auc);
  $("#prevalence").textContent = formatPct(anomalyRate);
  $("#method-count").textContent = names.length;
  updateSelected(best);
}

function renderRows() {
  const rows = methodNames().sort((a, b) => metrics[b].roc_auc - metrics[a].roc_auc);
  $("#detector-rows").innerHTML = rows.map((name, index) => {
    const item = metrics[name];
    const meta = METHOD_LABELS[name] || {};
    return `<div class="detector-row${name === selectedMethod ? " selected" : ""}" data-method="${name}" tabindex="0" role="button" aria-label="Select ${titleCase(name)}">
      <div class="method-cell"><span class="method-rank">0${index + 1}</span><span class="method-dot"></span><span class="method-name">${meta.label || titleCase(name)} <span class="method-tag">${meta.short || ""}</span></span></div>
      <span class="metric-number">${formatScore(item.roc_auc)}</span><span class="metric-number">${formatScore(item.average_precision)}</span><span class="metric-number">${formatScore(item.f1)}</span><span class="flag-pill">${item.flagged}</span>
    </div>`;
  }).join("");
  document.querySelectorAll(".detector-row").forEach((row) => {
    row.addEventListener("click", () => updateSelected(row.dataset.method));
    row.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); updateSelected(row.dataset.method); } });
  });
}

function renderCategoryBars() {
  const names = methodNames().sort((a, b) => metrics[b].roc_auc - metrics[a].roc_auc);
  $("#category-bars").innerHTML = names.map((name) => {
    const label = titleCase(name);
    const values = metrics.category_recall[name];
    return `<div class="bar-method"><div class="bar-method-head"><span>${label}</span><span>${METHOD_LABELS[name]?.short || ""}</span></div>${Object.keys(CATEGORY_LABELS).map((category) => `<div class="bar-group"><span class="bar-label">${CATEGORY_LABELS[category]}</span><span class="bar-track"><span class="bar-fill ${category}" style="width:${Math.max(2, values[category] * 100)}%"></span></span><span class="bar-value">${formatPct(values[category])}</span></div>`).join("")}</div>`;
  }).join("");
}

function updateSelected(name) {
  if (!metrics?.[name]) return;
  selectedMethod = name;
  const item = metrics[name];
  const recall = item.recall;
  $("#selected-method").textContent = titleCase(name);
  $("#selected-pill").textContent = titleCase(name);
  $("#insight-title").textContent = `${titleCase(name)} makes the clearest cut.`;
  $("#insight-copy").textContent = name === "elliptic_envelope"
    ? "The strongest aggregate result in this run: robust covariance captures the shifted cluster while keeping the fixed budget precise."
    : `${METHOD_LABELS[name]?.note || "This detector"} produces a distinct ranking profile; inspect the category bars before trusting the aggregate score.`;
  $("#queue-recall").textContent = formatPct(recall);
  $("#queue-precision").textContent = formatPct(item.precision);
  renderRows();
  syncSimulation();
}

function syncSimulation() {
  if (!metrics?.[selectedMethod]) return;
  const item = metrics[selectedMethod];
  const threshold = Number($("#threshold").value) / 100;
  const budget = Number($("#flag-budget").value);
  const baselineBudget = Math.max(1, item.flagged || 100);
  const thresholdFactor = 1 - Math.max(0, threshold - 0.70) * 0.8 + Math.max(0, 0.70 - threshold) * 0.25;
  const budgetFactor = Math.min(1.2, Math.max(.45, budget / baselineBudget));
  const projectedRecall = Math.min(.99, Math.max(.03, item.recall * thresholdFactor * Math.min(1.08, budgetFactor)));
  const projectedPrecision = Math.min(.99, Math.max(.08, item.precision * (thresholdFactor * .72 + .28) * (budgetFactor > 1 ? 1 - (budgetFactor - 1) * .14 : 1 + (1 - budgetFactor) * .12)));
  $("#threshold-output").textContent = threshold.toFixed(2);
  $("#budget-output").textContent = `${budget} points`;
  $("#budget-summary").textContent = budget;
  $("#queue-flagged").textContent = budget;
  $("#queue-recall").textContent = formatPct(projectedRecall);
  $("#queue-precision").textContent = formatPct(projectedPrecision);
  $("#queue-fill").style.width = `${Math.min(100, budget / 2)}%`;
  $("#queue-note").textContent = budget === baselineBudget && threshold === .70
    ? `At ${budget} flags, the UI mirrors the saved fixed-budget result. Move the controls to explore a directional trade-off.`
    : `Illustrative preview: threshold ${threshold.toFixed(2)} and a ${budget}-point queue. The Python experiment is not rerun in the browser.`;
}

async function loadMetrics() {
  try {
    const response = await fetch("artifacts/metrics.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    metrics = await response.json();
    renderSummary();
    renderCategoryBars();
  } catch (error) {
    $("#detector-rows").innerHTML = `<div class="loading-row">Could not load <code>artifacts/metrics.json</code>. Run <code>python3 -m http.server</code> from this project directory, then refresh.</div>`;
    $("#category-bars").innerHTML = `<div class="loading-row">Dashboard data unavailable until the local server is running.</div>`;
    console.error("Metrics load failed", error);
  }
}

$("#threshold").addEventListener("input", syncSimulation);
$("#flag-budget").addEventListener("input", syncSimulation);
loadMetrics();
