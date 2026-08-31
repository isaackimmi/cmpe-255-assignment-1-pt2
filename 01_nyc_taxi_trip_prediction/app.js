const fallbackMetrics = {
  rows_after_cleaning: 5996, train_rows: 4749, test_rows: 1199, test_rows_robust_inlier: 1186,
  baseline_median_seconds: 576,
  baseline: { mae_seconds: 148.243, rmse_seconds: 184.684, r2: -0.0083 },
  linear_log_target: { mae_seconds: 84.592, rmse_seconds: 106.976, r2: 0.6617 },
  source: "deterministic synthetic NYC-like fallback",
};

let metrics = fallbackMetrics;
let predictionRows = [];
let importanceRows = [];
const $ = (selector) => document.querySelector(selector);
const $all = (selector) => [...document.querySelectorAll(selector)];
const setMetric = (key, value) => $all(`[data-metric="${key}"]`).forEach((node) => { node.textContent = value; });
const formatNumber = (value, digits = 3) => Number(value).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
const formatMetric = (value, metric) => metric === "r2" ? Number(value).toFixed(4) : formatNumber(value);
const comparisonColumns = { global_median: "global_median_seconds", recent_median_baseline: "recent_median_seconds", hour_median_baseline: "hour_median_seconds" };
const methodLabels = { global_median: "GLOBAL MEDIAN", recent_median_baseline: "RECENT MEDIAN", hour_median_baseline: "HOUR-CONDITIONED MEDIAN" };
const foldMethods = { global_median: "global_median", recent_median_baseline: "recent_median", hour_median_baseline: "hour_median" };

function renderMetrics(next) {
  metrics = next;
  const model = metrics.linear_log_target;
  const baseline = metrics.baseline;
  const improvement = ((baseline.mae_seconds - model.mae_seconds) / baseline.mae_seconds) * 100;
  setMetric("model-mae", formatNumber(model.mae_seconds));
  setMetric("baseline-mae", formatNumber(baseline.mae_seconds));
  setMetric("improvement", improvement.toFixed(1));
  setMetric("r2", Number(model.r2).toFixed(4));
  setMetric("rows", Number(metrics.rows_after_cleaning).toLocaleString());
  setMetric("split", `${Number(metrics.train_rows).toLocaleString()} / ${Number(metrics.test_rows).toLocaleString()}`);
  setMetric("mae-delta", formatNumber(baseline.mae_seconds - model.mae_seconds));
  $all("[data-source]").forEach((node) => { node.textContent = metrics.source || fallbackMetrics.source; });
  const heroOrbit = $(".hero-orbit");
  if (heroOrbit) heroOrbit.setAttribute("aria-label", `Experiment result: model MAE ${formatNumber(model.mae_seconds)} seconds`);
  const baselineBar = $(".bar-baseline");
  const modelBar = $(".bar-model");
  if (baselineBar && modelBar) { baselineBar.style.width = "100%"; modelBar.style.width = `${Math.max(8, (model.mae_seconds / baseline.mae_seconds) * 100)}%`; }
}

function scoreRows(rows, predictionColumn, metric) {
  if (!rows.length) return null;
  const actual = rows.map((row) => Number(row.actual_seconds));
  const predicted = rows.map((row) => Number(row[predictionColumn]));
  if (metric === "mae_seconds") return actual.reduce((sum, value, index) => sum + Math.abs(value - predicted[index]), 0) / rows.length;
  if (metric === "rmse_seconds") return Math.sqrt(actual.reduce((sum, value, index) => sum + (value - predicted[index]) ** 2, 0) / rows.length);
  const mean = actual.reduce((sum, value) => sum + value, 0) / rows.length;
  const total = actual.reduce((sum, value) => sum + (value - mean) ** 2, 0);
  return total ? 1 - actual.reduce((sum, value, index) => sum + (value - predicted[index]) ** 2, 0) / total : 0;
}

function drawResidualChart(rows) {
  const svg = $("#residual-chart");
  if (!svg) return;
  if (!rows.length) { svg.innerHTML = '<text class="chart-empty" x="20" y="95">No rows match this selection.</text>'; return; }
  const values = rows.map((row) => Number(row.residual_seconds));
  const lo = Math.min(...values, 0); const hi = Math.max(...values, 0);
  const bins = Array.from({ length: 24 }, () => 0);
  values.forEach((value) => bins[Math.min(23, Math.floor((value - lo) / (hi - lo + 1e-9) * 24))]++);
  const peak = Math.max(...bins, 1);
  const bars = bins.map((count, index) => { const height = count / peak * 132; return `<rect x="${24 + index * 23}" y="${157 - height}" width="17" height="${height}" class="residual-bar"><title>${count} rows</title></rect>`; }).join("");
  const zeroX = 24 + ((0 - lo) / (hi - lo + 1e-9)) * 552;
  svg.innerHTML = `${bars}<line class="residual-zero" x1="${zeroX}" y1="18" x2="${zeroX}" y2="160" /><line class="residual-axis" x1="24" y1="160" x2="576" y2="160" /><text class="chart-label" x="24" y="180">${Math.round(lo)} sec</text><text class="chart-label" x="538" y="180">${Math.round(hi)} sec</text><text class="chart-label" x="${Math.max(28, zeroX - 17)}" y="14">zero</text>`;
}

function selectedExplorerRows() {
  const population = $("#explorer-population")?.value || "primary";
  const slice = $("#explorer-slice")?.value || "all";
  const distances = predictionRows.map((row) => Number(row.distance_miles)).sort((a, b) => a - b);
  const distanceMedian = distances.length ? distances[Math.floor(distances.length / 2)] : 0;
  return predictionRows.filter((row) => {
    if (population === "robust" && row.robust_inlier !== "1") return false;
    const rush = [7, 8, 9, 16, 17, 18, 19].includes(Number(row.hour));
    if (slice === "rush") return rush;
    if (slice === "off_peak") return !rush;
    if (slice === "short") return Number(row.distance_miles) < distanceMedian;
    if (slice === "long") return Number(row.distance_miles) >= distanceMedian;
    if (slice === "weekend") return row.is_weekend === "1";
    if (slice === "weekday") return row.is_weekend !== "1";
    return true;
  });
}

function renderExplorer() {
  const rows = selectedExplorerRows();
  const metric = $("#explorer-metric")?.value || "mae_seconds";
  const comparison = $("#explorer-comparison")?.value || "global_median";
  const modelValue = scoreRows(rows, "predicted_seconds", metric);
  const baselineValue = scoreRows(rows, comparisonColumns[comparison], metric);
  const sliceText = $("#explorer-slice")?.selectedOptions[0]?.textContent || "Selected slice";
  const populationText = $("#explorer-population")?.selectedOptions[0]?.textContent || "holdout rows";
  $("#explorer-slice-title").textContent = sliceText;
  $("#explorer-count").textContent = `${rows.length.toLocaleString()} rows`;
  $("#explorer-model-value").textContent = modelValue === null ? "—" : formatMetric(modelValue, metric);
  $("#explorer-baseline-value").textContent = baselineValue === null ? "—" : formatMetric(baselineValue, metric);
  $("#explorer-comparator-label").textContent = methodLabels[comparison];
  $("#explorer-note").textContent = predictionRows.length ? `${metric === "r2" ? "R²" : metric.startsWith("rmse") ? "RMSE" : "MAE"} recomputed for ${populationText.toLowerCase()}. Residuals are predicted minus actual seconds.` : "Serve this folder locally to load the checked-in predictions artifact.";
  drawResidualChart(rows);
  renderFoldTable(metric, comparison);
}

function renderFoldTable(metric, comparison) {
  const body = $("#fold-table-body");
  const folds = metrics.temporal_validation?.folds || [];
  const robust = $("#explorer-population")?.value === "robust";
  if (!folds.length) { body.innerHTML = '<tr><td colspan="5">Fold metadata unavailable in preview mode.</td></tr>'; return; }
  body.innerHTML = folds.map((fold) => {
    const source = robust ? fold.robust_inlier : fold;
    const model = source?.linear_log_target?.[metric];
    const baseline = source?.[foldMethods[comparison]]?.[metric];
    const cutoff = fold.split_cutoff?.test_min_pickup_datetime || "—";
    return `<tr><td>0${fold.fold}</td><td>${fold.train_rows} / ${robust ? fold.robust_test_rows : fold.test_rows}</td><td>${cutoff.slice(0, 10)}</td><td>${model === undefined ? "—" : formatMetric(model, metric)}</td><td>${baseline === undefined ? "—" : formatMetric(baseline, metric)}</td></tr>`;
  }).join("");
}

function renderImportance() {
  const body = $("#importance-table-body");
  if (!importanceRows.length) { body.innerHTML = '<tr><td colspan="2">Feature artifact unavailable in preview mode.</td></tr>'; return; }
  body.innerHTML = importanceRows.slice(0, 8).map((row) => `<tr><td>${row.feature}</td><td>${formatNumber(Number(row.standardized_abs_coefficient))}</td></tr>`).join("");
}

function renderAudit() {
  const target = metrics.target_policy || {};
  const drops = Object.entries(metrics.dropped_by_reason || {});
  const dropText = drops.length ? drops.map(([reason, count]) => `${reason}: ${count}`).join(" · ") : "none";
  const sourceHash = metrics.source_sha256 ? `${metrics.source_sha256.slice(0, 12)}…` : "synthetic fallback · no source hash";
  $("#audit-summary").innerHTML = `<dl><div><dt>Primary score</dt><dd>${Number(metrics.test_rows || 0).toLocaleString()} eligible future rows</dd></div><div><dt>Inlier sensitivity</dt><dd>${Number(metrics.test_rows_robust_inlier || 0).toLocaleString()} rows below train-only threshold</dd></div><div><dt>Fit population</dt><dd>${Number(metrics.train_rows || 0).toLocaleString()} rows</dd></div><div><dt>Structural drops</dt><dd>${dropText}</dd></div><div><dt>Source</dt><dd>${sourceHash}</dd></div><div><dt>Run UTC</dt><dd>${metrics.run_timestamp_utc || "preview values"}</dd></div></dl>`;
}

function haversineMiles(lat1, lon1, lat2, lon2) {
  const rad = Math.PI / 180; const dLat = (lat2 - lat1) * rad; const dLon = (lon2 - lon1) * rad;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
  return 3958.8 * 2 * Math.asin(Math.sqrt(Math.max(0, Math.min(1, a))));
}

function drawEstimateChart(seconds, isRush) {
  const svg = $("#estimate-chart");
  const points = Array.from({ length: 7 }, (_, index) => { const x = 20 + index * 80; const wave = Math.sin(index * 1.1) * 7; const factor = 0.65 + index * 0.055; return [x, 103 - Math.min(63, (seconds / 720) * 63 * factor) + wave]; });
  const polyline = points.map(([x, y]) => `${x},${y}`).join(" "); const area = `20,112 ${polyline} 500,112`; const [lastX, lastY] = points[points.length - 1];
  svg.innerHTML = `<line class="chart-gridline" x1="20" y1="39" x2="500" y2="39" /><line class="chart-gridline" x1="20" y1="76" x2="500" y2="76" /><path class="chart-area" d="M${area}Z" /><polyline class="chart-line" points="${polyline}" /><circle class="chart-point" cx="${lastX}" cy="${lastY}" r="5" /><text class="chart-label" x="20" y="126">pickup</text><text class="chart-label" x="448" y="126">drop-off</text><text class="chart-label" x="405" y="20">${isRush ? "rush-hour lift" : "off-peak baseline"}</text>`;
}

function updateEstimate(event) {
  if (event) event.preventDefault();
  const form = new FormData($("#estimator-form"));
  const values = ["pickupLongitude", "pickupLatitude", "dropoffLongitude", "dropoffLatitude"].map((name) => Number(form.get(name)));
  const [pickupLon, pickupLat, dropoffLon, dropoffLat] = values; const passengers = Number(form.get("passengers")); const pickup = new Date(form.get("pickupTime")); const error = $("#estimator-error");
  const invalid = values.some((value) => !Number.isFinite(value)) || pickup.toString() === "Invalid Date" || passengers < 1 || passengers > 10 || pickupLon < -74.3 || pickupLon > -73.65 || dropoffLon < -74.3 || dropoffLon > -73.65 || pickupLat < 40.45 || pickupLat > 40.95 || dropoffLat < 40.45 || dropoffLat > 40.95;
  if (invalid) { error.textContent = "Use a valid date and coordinates inside the NYC-like service area."; $("#estimate-value").textContent = "—:—"; return; }
  error.textContent = "";
  const distance = haversineMiles(pickupLat, pickupLon, dropoffLat, dropoffLon); const hour = pickup.getHours(); const isRush = [7, 8, 9, 16, 17, 18, 19].includes(hour); const isWeekend = [0, 6].includes(pickup.getDay());
  const seconds = Math.max(60, Math.round(240 + 115 * distance + (isRush ? 90 : 0) + 25 * Math.max(0, passengers - 1) + (isWeekend ? -12 : 0))); const mins = String(Math.floor(seconds / 60)).padStart(2, "0"); const secs = String(seconds % 60).padStart(2, "0");
  $("#estimate-value").textContent = `${mins}:${secs}`; $("#distance-value").textContent = distance.toFixed(1); $("#context-value").textContent = isRush ? "rush-hour" : "off-peak"; $("#rush-status").textContent = isRush ? "rush hour" : "off-peak"; $("#rush-status").classList.toggle("quiet", !isRush); $("#estimate-summary").textContent = `A ${distance.toFixed(1)} mi trip with ${passengers} passenger${passengers === 1 ? "" : "s"}, leaving ${isRush ? "during the evening commute" : "outside the rush-hour window"}.`; drawEstimateChart(seconds, isRush);
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/); if (lines.length < 2) return []; const headers = lines.shift().split(",");
  return lines.map((line) => line.split(",")).map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index]])));
}

async function loadOutputs() {
  try {
    const [metricsResponse, predictionsResponse, importanceResponse] = await Promise.all([fetch("outputs/metrics.json", { cache: "no-store" }), fetch("outputs/predictions.csv", { cache: "no-store" }), fetch("outputs/feature_importance.csv", { cache: "no-store" })]);
    if (!metricsResponse.ok || !predictionsResponse.ok || !importanceResponse.ok) throw new Error("artifact unavailable");
    renderMetrics(await metricsResponse.json()); predictionRows = parseCsv(await predictionsResponse.text()); importanceRows = parseCsv(await importanceResponse.text()); $("#run-status").textContent = "artifacts loaded"; $("#data-status").textContent = "live artifacts · metrics.json / predictions.csv"; renderAudit(); renderImportance(); renderExplorer();
  } catch (error) {
    renderMetrics(fallbackMetrics); predictionRows = []; importanceRows = []; $("#run-status").textContent = "preview / fallback"; $("#data-status").textContent = "preview values · serve folder to load artifacts"; renderAudit(); renderImportance(); renderExplorer();
  }
}

$("#estimator-form").addEventListener("submit", updateEstimate); $("#estimator-form").addEventListener("input", updateEstimate);
["#explorer-metric", "#explorer-comparison", "#explorer-population", "#explorer-slice"].forEach((selector) => $(selector).addEventListener("change", renderExplorer));
$all(".copy-button").forEach((button) => button.addEventListener("click", async () => { try { await navigator.clipboard.writeText(button.dataset.copy); button.textContent = "copied"; setTimeout(() => { button.textContent = "copy"; }, 1200); } catch { button.textContent = "select"; } }));

renderMetrics(fallbackMetrics); renderAudit(); renderImportance(); renderExplorer(); updateEstimate(); loadOutputs();
