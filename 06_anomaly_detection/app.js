const METHOD_LABELS = {
  isolation_forest: { label: "Isolation Forest", short: "IF", note: "Random partitions" },
  local_outlier_factor: { label: "Local Outlier Factor", short: "LOF", note: "Density contrast" },
  elliptic_envelope: { label: "Elliptic Envelope", short: "EE", note: "Robust covariance" },
  rank_ensemble: { label: "Rank ensemble", short: "ENSEMBLE", note: "Percentile blend" },
};
const CATEGORY_LABELS = { global: "Global", local: "Local", cluster: "Cluster" };
const CATEGORY_COLORS = { normal: "#8994a7", global: "#7cc7ff", local: "#ff9d5c", cluster: "#b0a6ff" };
let metrics = null;
let observations = [];
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
  $("#hero-train-size").textContent = metadata.train_size || "—";
  $("#hero-calibration-size").textContent = metadata.calibration_size || "—";
  $("#hero-test-size").textContent = metadata.test_size || "—";
  $("#holdout-size-methodology").textContent = metadata.test_size || "—";
  $("#seed-label").textContent = metadata.seed ?? "—";
  $("#seed-label-foot").textContent = metadata.seed ?? "—";
  $("#run-id").textContent = String(metadata.seed ?? "—").padStart(3, "0");
  $("#seed-stamp").textContent = metadata.seed ?? "—";
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

function thresholdPoint(name, percentile) {
  return metrics.threshold_points?.[name]?.find((point) => point.percentile === percentile);
}

function operatingPoint(name, percentile, budget) {
  return metrics.operating_points?.[name]?.[String(percentile)]?.[String(budget)];
}

function currentFlaggedRows() {
  const percentile = Number($("#threshold").value);
  const budget = Number($("#flag-budget").value);
  const threshold = thresholdPoint(selectedMethod, percentile);
  const point = operatingPoint(selectedMethod, percentile, budget);
  if (!threshold || !point || !observations.length) return [];
  return observations
    .map((observation, index) => ({ observation, index, score: Number(observation.scores[selectedMethod]) }))
    .filter((row) => row.score >= threshold.threshold)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .slice(0, point.flagged);
}

function renderCategoryBars() {
  const names = methodNames();
  if (!names.length) return;
  const flaggedRows = currentFlaggedRows();
  const counts = Object.fromEntries(Object.keys(CATEGORY_LABELS).map((category) => [category, 0]));
  const denominators = Object.fromEntries(Object.keys(CATEGORY_LABELS).map((category) => [category, 0]));
  observations.forEach((observation) => {
    if (observation.label === 1 && counts[observation.category] !== undefined) denominators[observation.category] += 1;
  });
  flaggedRows.forEach(({ observation }) => { if (counts[observation.category] !== undefined) counts[observation.category] += 1; });
  const fallback = metrics.category_recall?.[selectedMethod] || {};
  const values = Object.fromEntries(Object.keys(CATEGORY_LABELS).map((category) => [
    category,
    denominators[category] ? counts[category] / denominators[category] : (fallback[category] || 0),
  ]));
  $("#category-bars").innerHTML = `<div class="bar-method"><div class="bar-method-head"><span>${titleCase(selectedMethod)}</span><span>SELECTED POINT</span></div>${Object.keys(CATEGORY_LABELS).map((category) => `<div class="bar-group"><span class="bar-label">${CATEGORY_LABELS[category]}</span><span class="bar-track"><span class="bar-fill ${category}" style="width:${Math.max(2, values[category] * 100)}%"></span></span><span class="bar-value">${formatPct(values[category])}</span></div>`).join("")}</div>`;
  $("#category-recall-note").textContent = observations.length
    ? "Recall updates with the selected detector, calibration percentile, and alert cap."
    : "Loading per-observation scores for selected-point recall…";
}

function renderScoreExplorer() {
  const percentile = Number($("#threshold").value);
  const budget = Number($("#flag-budget").value);
  const threshold = thresholdPoint(selectedMethod, percentile);
  const point = operatingPoint(selectedMethod, percentile, budget);
  if (!threshold || !point || !observations.length) return;
  const rows = observations
    .map((observation, index) => ({ observation, index, score: Number(observation.scores[selectedMethod]) }))
    .sort((a, b) => b.score - a.score || a.index - b.index);
  const flagged = new Set(currentFlaggedRows().map((row) => row.index));
  const width = 760;
  const height = 230;
  const left = 42;
  const right = 14;
  const top = 14;
  const bottom = 30;
  const min = Math.min(...rows.map((row) => row.score), threshold.threshold);
  const max = Math.max(...rows.map((row) => row.score), threshold.threshold);
  const range = max > min ? max - min : 1;
  const xFor = (index) => left + index * ((width - left - right) / Math.max(1, rows.length - 1));
  const yFor = (score) => top + (max - score) / range * (height - top - bottom);
  const thresholdY = yFor(threshold.threshold);
  const circles = rows.map((row, index) => {
    const observation = row.observation;
    const isFlagged = flagged.has(row.index);
    const color = CATEGORY_COLORS[observation.category] || CATEGORY_COLORS.normal;
    return `<circle cx="${xFor(index).toFixed(2)}" cy="${yFor(row.score).toFixed(2)}" r="${isFlagged ? 4.1 : 2.5}" fill="${color}" stroke="${isFlagged ? "#c8f36a" : "none"}" stroke-width="${isFlagged ? 1.5 : 0}"><title>${observation.id} · ${observation.category} · score ${formatScore(row.score)}${isFlagged ? " · flagged" : ""}</title></circle>`;
  }).join("");
  $("#score-plot").innerHTML = `<line class="plot-axis" x1="${left}" y1="${height - bottom}" x2="${width - right}" y2="${height - bottom}" /><line class="plot-threshold" x1="${left}" y1="${thresholdY.toFixed(2)}" x2="${width - right}" y2="${thresholdY.toFixed(2)}" /><text class="plot-threshold-label" x="${width - right - 4}" y="${Math.max(12, thresholdY - 6)}" text-anchor="end">${percentile}% calibration cut</text>${circles}<text class="plot-label" x="${left}" y="${height - 8}">rank 1</text><text class="plot-label" x="${width - right}" y="${height - 8}" text-anchor="end">rank ${rows.length}</text>`;
  $("#score-caption").textContent = `${titleCase(selectedMethod)} scores sorted high to low. Lime outlines are the ${point.flagged}-row saved operating-point queue; colors show holdout mechanism.`;
  const tableRows = currentFlaggedRows().slice(0, 8).map(({ observation, score }) => `<tr><td>${observation.id}</td><td>${CATEGORY_LABELS[observation.category] || "Normal"}</td><td>${formatScore(score)}</td><td><span class="alert-state">FLAGGED</span></td></tr>`).join("");
  $("#alert-rows").innerHTML = tableRows || `<tr><td colspan="4">No rows cross this saved operating point.</td></tr>`;
}

function updateSelected(name) {
  if (!metrics?.[name]) return;
  selectedMethod = name;
  const item = metrics[name];
  const names = methodNames();
  const best = names.reduce((winner, method) => metrics[method].roc_auc > metrics[winner].roc_auc ? method : winner, names[0]);
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
  $("#queue-note").textContent = `Saved holdout replay: score ≥ ${threshold.threshold.toFixed(3)} (${percentile}th percentile of clean calibration), capped at ${budget} alerts. Labels are used only for this offline evaluation; do not tune a production threshold from this holdout.`;
  renderCategoryBars();
  renderScoreExplorer();
}

async function loadMetrics() {
  try {
    const [metricsResponse, observationsResponse] = await Promise.all([
      fetch("artifacts/metrics.json", { cache: "no-store" }),
      fetch("artifacts/observations.json", { cache: "no-store" }),
    ]);
    if (!metricsResponse.ok) throw new Error(`metrics HTTP ${metricsResponse.status}`);
    if (!observationsResponse.ok) throw new Error(`observations HTTP ${observationsResponse.status}`);
    metrics = await metricsResponse.json();
    observations = await observationsResponse.json();
    renderSummary();
    renderCategoryBars();
  } catch (error) {
    $("#detector-rows").innerHTML = `<div class="loading-row">Could not load the saved metric/score artifacts. Regenerate <code>artifacts/metrics.json</code> and <code>artifacts/observations.json</code>.</div>`;
    $("#category-bars").innerHTML = `<div class="loading-row">Score explorer unavailable until the saved artifacts are present.</div>`;
    console.error("Metrics load failed", error);
  }
}

$("#threshold").addEventListener("input", syncSimulation);
$("#flag-budget").addEventListener("input", syncSimulation);
loadMetrics();
