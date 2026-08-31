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
  if (!names.length) return;
  const best = names.reduce((winner, name) => metrics[name].roc_auc > metrics[winner].roc_auc ? name : winner, names[0]);
  const metadata = metrics.metadata || {};
  const anomalyRate = Number(metadata.test_anomaly_rate || 0);
  $("#best-method").textContent = titleCase(best);
  $("#best-auc").textContent = formatScore(metrics[best].roc_auc);
  $("#prevalence").textContent = formatPct(anomalyRate);
  $("#method-count").textContent = names.length;
  $("#budget-summary").textContent = metadata.alert_budget || 100;
  $("#dataset-size").textContent = metadata.test_size || "—";
  $("#dataset-size-rail").textContent = metadata.test_size || "—";
  $("#anomaly-count").textContent = metadata.test_anomaly_count || "—";
  $("#train-size").textContent = metadata.train_size || "—";
  $("#calibration-size").textContent = metadata.calibration_size || "—";
  $("#seed-label").textContent = metadata.seed ?? "—";
  $("#seed-label-foot").textContent = metadata.seed ?? "—";
  $("#run-id").textContent = String(metadata.seed ?? "—").padStart(3, "0");
  const generated = metadata.generated_at_utc ? new Date(metadata.generated_at_utc) : null;
  $("#run-time").textContent = generated && !Number.isNaN(generated.valueOf())
    ? `GENERATED ${generated.toLocaleString()}`
    : "GENERATED FROM ARTIFACT";
  updateSelected(best);
}

function renderRows() {
  const rows = methodNames().sort((a, b) => metrics[b].roc_auc - metrics[a].roc_auc);
  $("#detector-rows").innerHTML = rows.map((name, index) => {
    const item = metrics[name];
    const meta = METHOD_LABELS[name] || {};
    return `<div class="detector-row${name === selectedMethod ? " selected" : ""}" data-method="${name}" tabindex="0" role="button" aria-label="Select ${titleCase(name)}">
      <div class="method-cell"><span class="method-rank">${String(index + 1).padStart(2, "0")}</span><span class="method-dot"></span><span class="method-name">${meta.label || titleCase(name)} <span class="method-tag">${meta.short || ""}</span></span></div>
      <span class="metric-number">${formatScore(item.roc_auc)}</span><span class="metric-number">${formatScore(item.average_precision)}</span><span class="metric-number">${formatScore(item.f1_at_k)}</span><span class="flag-pill">${item.flagged}</span>
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
    const values = metrics.category_recall[name];
    return `<div class="bar-method"><div class="bar-method-head"><span>${titleCase(name)}</span><span>${METHOD_LABELS[name]?.short || ""}</span></div>${Object.keys(CATEGORY_LABELS).map((category) => `<div class="bar-group"><span class="bar-label">${CATEGORY_LABELS[category]}</span><span class="bar-track"><span class="bar-fill ${category}" style="width:${Math.max(2, values[category] * 100)}%"></span></span><span class="bar-value">${formatPct(values[category])}</span></div>`).join("")}</div>`;
  }).join("");
}

function thresholdPoint(name, percentile) {
  return metrics.threshold_points?.[name]?.find((point) => point.percentile === percentile);
}

function operatingPoint(name, percentile, budget) {
  return metrics.operating_points?.[name]?.[String(percentile)]?.[String(budget)];
}

function updateSelected(name) {
  if (!metrics?.[name]) return;
  selectedMethod = name;
  const item = metrics[name];
  const best = methodNames().reduce((winner, method) => metrics[method].roc_auc > metrics[winner].roc_auc ? method : winner, methodNames()[0]);
  $("#selected-method").textContent = titleCase(name);
  $("#selected-pill").textContent = titleCase(name);
  $("#insight-title").textContent = name === best ? `${titleCase(name)} leads holdout ROC-AUC.` : `${titleCase(name)} shows a distinct signal.`;
  $("#insight-copy").textContent = name === best
    ? "Highest ROC-AUC in this labeled synthetic holdout. Treat the result as a single-seed comparison, not a universal ranking."
    : `${METHOD_LABELS[name]?.note || "This detector"} produces a distinct ranking profile; inspect category recall before trusting the aggregate score.`;
  $("#queue-recall").textContent = formatPct(item.recall_at_k);
  $("#queue-precision").textContent = formatPct(item.precision_at_k);
  renderRows();
  syncSimulation();
}

function syncSimulation() {
  if (!metrics?.[selectedMethod]) return;
  const percentile = Number($("#threshold").value);
  const budget = Number($("#flag-budget").value);
  const point = operatingPoint(selectedMethod, percentile, budget);
  const threshold = thresholdPoint(selectedMethod, percentile);
  if (!point || !threshold) return;
  $("#threshold-output").textContent = `${percentile}% clean calibration`;
  $("#budget-output").textContent = `${budget} point cap`;
  $("#queue-flagged").textContent = point.flagged;
  $("#queue-recall").textContent = formatPct(point.recall);
  $("#queue-precision").textContent = formatPct(point.precision);
  $("#queue-fill").style.width = `${Math.min(100, (point.flagged / budget) * 100)}%`;
  $("#queue-note").textContent = `Saved holdout replay: score ≥ ${threshold.threshold.toFixed(3)} (${percentile}th percentile of clean calibration), capped at ${budget} alerts. Labels are used only in this offline evaluation. `;
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
