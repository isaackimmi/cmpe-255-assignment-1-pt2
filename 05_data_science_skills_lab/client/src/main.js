import "./style.css";

const state = { data: null, module: "overview", plan: "all", renewal: "all", cluster: "all", loading: false };
const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const app = document.querySelector("#app");
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>\"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char]));
const pct = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`;
const num = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "—";

function metric(label, value, note, accent = "") { return `<article class="metric ${accent}"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`; }

function shell() {
  app.innerHTML = `<div class="app-shell"><aside class="sidebar"><div class="brand"><span class="brand-mark">05</span><div><b>signal/</b><small>DATA SCIENCE SKILLS LAB</small></div></div><p class="eyebrow">CRISP-DM WORKBENCH</p><nav aria-label="Lab modules"><button data-module="overview" class="nav-button active">Overview <span>↗</span></button><button data-module="cleaning" class="nav-button">01 · Clean & validate</button><button data-module="classification" class="nav-button">02 · Classification</button><button data-module="regression" class="nav-button">03 · Regression</button><button data-module="clustering" class="nav-button">04 · Clustering</button></nav><div class="sidebar-note"><span class="pulse"></span><b>Offline artifact mode</b><small>FastAPI serves checked-in experiment evidence. No browser-side model fitting.</small></div></aside><main><header class="topbar"><span>PROJECT 05 / ANALYTICS LAB</span><span id="api-status" class="status">CONNECTING…</span></header><section class="hero"><div><p class="eyebrow accent">A DATA SCIENCE TOOLKIT, MADE INSPECTABLE</p><h1>From messy rows<br><em>to useful signal.</em></h1><p class="lede">An end-to-end lab for seeing how cleaning, evaluation, regression, classification, and clustering change the story a dataset can tell.</p></div><div class="hero-orbit"><span>CSV</span><i>→</i><strong>DS</strong><i>→</i><span>INSIGHT</span></div></section><section id="metrics" class="metrics"></section><section class="workspace"><div class="workspace-head"><div><p class="eyebrow accent">LIVE EXPLORER</p><h2 id="module-title">What the run actually measured.</h2><p id="module-copy" class="muted">Select a module to inspect its assumptions, metrics, and observed rows.</p></div><div class="filters"><label>Plan<select id="plan-filter"><option value="all">All plans</option><option>basic</option><option>pro</option><option>enterprise</option></select></label><label>Renewal<select id="renewal-filter"><option value="all">All outcomes</option><option value="1">Renewed</option><option value="0">Not renewed</option></select></label><label>Cluster<select id="cluster-filter"><option value="all">All groups</option><option value="0">Cluster 0</option><option value="1">Cluster 1</option></select></label></div></div><div id="workspace-content"></div></section><section class="method"><div><p class="eyebrow accent">WHY THIS MATTERS</p><h2>Metrics are only useful<br><em>when their boundaries are visible.</em></h2></div><div class="method-grid"><article><b>01</b><h3>Fit on train</h3><p>Feature medians are learned from training rows, then applied to the holdout. Missing targets are never fabricated for scoring.</p></article><article><b>02</b><h3>Compare baselines</h3><p>Every model view keeps a simple reference point nearby so improvement is measurable rather than implied.</p></article><article><b>03</b><h3>Interpret, don’t overclaim</h3><p>The CSV is a synthetic teaching fixture. Correlations and segments are descriptive, not causal or production evidence.</p></article></div></section><footer>PROJECT 05 · LOCAL ARTIFACT WORKBENCH <span>seed 255 · standard-library ML</span></footer></main></div>`;
  document.querySelectorAll("[data-module]").forEach((button) => button.addEventListener("click", async () => { state.module = button.dataset.module; document.querySelectorAll("[data-module]").forEach((item) => item.classList.toggle("active", item === button)); await loadModule(state.module); }));
  ["plan", "renewal", "cluster"].forEach((name) => $(`#${name}-filter`).addEventListener("change", async (event) => { state[name] = event.target.value; try { await loadRows(); render(); } catch (error) { showError(error); } }));
}

async function fetchJSON(path) {
  const response = await fetch(`${API_BASE}${path}`, { headers: { Accept: "application/json" } });
  let body = null;
  try { body = await response.json(); } catch { body = {}; }
  if (!response.ok) throw new Error(body.detail || `API ${response.status}`);
  return body;
}

function showError(error) {
  $("#api-status").textContent = "○ API ERROR";
  $("#api-status").classList.remove("ready");
  $("#workspace-content").innerHTML = `<div class="empty"><h3>Evidence request failed.</h3><p>${esc(error.message)} · No model result was fabricated in the browser.</p><button id="retry-api" class="nav-button">Retry request ↗</button></div>`;
  $("#retry-api").addEventListener("click", () => loadModule(state.module));
}

async function load() {
  try { state.data = await fetchJSON("/api/summary"); await loadRows(); $("#api-status").textContent = "● API CONNECTED · OVERVIEW"; $("#api-status").classList.add("ready"); render(); }
  catch (error) { showError(error); }
}

async function loadRows() {
  if (!state.data) return;
  const query = new URLSearchParams({ plan: state.plan, renewal: state.renewal, cluster: state.cluster, limit: "1000" });
  const result = await fetchJSON(`/api/rows?${query}`);
  state.data.summary.analysis_rows = result.rows;
  $("#api-status").textContent = `● API CONNECTED · ${result.count} ROWS`;
  $("#api-status").classList.add("ready");
}

async function loadModule(module) {
  if (module === "overview") { await load(); return; }
  const routes = { cleaning: "/api/cleaning", classification: "/api/classification", regression: "/api/regression", clustering: "/api/clustering" };
  $("#workspace-content").innerHTML = `<div class="empty"><h3>Loading ${esc(module)} evidence…</h3><p>FastAPI is returning the purpose-built analytical payload.</p></div>`;
  try {
    const result = await fetchJSON(routes[module]);
    if (module === "cleaning") state.data.metrics.data_quality = result;
    if (module === "classification") state.data.metrics.classification = result;
    if (module === "regression") { state.data.metrics.regression = result.metrics; state.data.summary.regression_predictions = result.predictions; state.data.summary.regression_excluded_test_targets = result.excluded_targets; }
    if (module === "clustering") { state.data.metrics.clustering = result.metrics; state.data.summary.analysis_rows = result.rows; }
    $("#api-status").textContent = `● API CONNECTED · ${module.toUpperCase()}`;
    $("#api-status").classList.add("ready");
    render();
  } catch (error) { showError(error); }
}

function filteredRows() { return state.data?.summary?.analysis_rows || []; }
function render() {
  if (!state.data) return;
  const { metrics, summary } = state.data; const rows = filteredRows(); const r = metrics.regression; const c = metrics.classification; const k = metrics.clustering;
  $("#metrics").innerHTML = [metric("CLEAN ROWS", metrics.data_quality.clean_rows, `${metrics.data_quality.duplicates_removed} duplicate removed`, "lime"), metric("CLASSIFICATION F1", num(c.f1), `accuracy ${pct(c.accuracy)}`), metric("REGRESSION MAE", num(r.mae), `baseline ${num(r.mean_baseline_mae)}`), metric("CLUSTER SILHOUETTE", num(k.silhouette), `${k.k} interpretable groups`)].join("");
  const labels = {overview:["What the run actually measured.","A compact view of the full pipeline and its evaluation boundaries."],cleaning:["Trust the rows first.","Validation, duplicates, missingness, and imputation are model inputs—not footnotes."],classification:["Who is likely to renew?","A fixed domain rule evaluated on a stratified holdout, with a majority-class baseline."],regression:["Usage has a shape.","A one-feature linear baseline predicts monthly usage from tenure on a seeded holdout."],clustering:["Find the natural groups.","Scaled usage and support-ticket behavior create descriptive customer segments without labels."]}; $("#module-title").textContent=labels[state.module][0]; $("#module-copy").textContent=labels[state.module][1]; $("#workspace-content").innerHTML = moduleMarkup(rows, metrics, summary); bindModule();
}
function moduleMarkup(rows, metrics, summary) {
  const r = metrics.regression, c = metrics.classification, k = metrics.clustering, q = metrics.data_quality;
  if (state.module === "cleaning") return `<div class="detail-grid"><article class="panel large"><div class="panel-top"><span class="tag">DATA QUALITY CONTRACT</span><strong>${q.clean_rows} clean rows</strong></div><div class="quality-grid">${Object.entries(q.missing_values_by_column).map(([key,value]) => `<div><span>${esc(key)}</span><b>${value} missing</b><small>${value ? "median-imputed where permitted" : "complete"}</small></div>`).join("")}</div><p class="callout">${esc(q.validation)}. Duplicate IDs are accepted only when records are identical.</p></article><article class="panel"><span class="tag">IMPUTATION</span><h3>Fit scope matters</h3><p>Global descriptive views use explicit medians. Predictive transforms fit medians on training rows and reuse them on the holdout.</p><dl><dt>Rows read</dt><dd>${q.raw_rows}</dd><dt>Duplicates removed</dt><dd>${q.duplicates_removed}</dd><dt>Values imputed</dt><dd>${q.missing_values_imputed}</dd></dl></article></div>`;
  if (state.module === "classification") return `<div class="detail-grid"><article class="panel large"><div class="panel-top"><span class="tag">FIXED DOMAIN RULE</span><strong>usage ≥ ${c.threshold}</strong></div><div class="confusion"><div><span>PREDICTED \ ACTUAL</span><b>0</b><b>1</b></div><div><span>0</span><b>${c.confusion_matrix[0][0]}</b><b>${c.confusion_matrix[0][1]}</b></div><div><span>1</span><b>${c.confusion_matrix[1][0]}</b><b>${c.confusion_matrix[1][1]}</b></div></div><p class="callout">${esc(c.rule)} · ${esc(c.threshold_source)}</p></article><article class="panel"><span class="tag">HOLDOUT METRICS</span><h3>${pct(c.balanced_accuracy)} balanced accuracy</h3>${[["Precision",c.precision],["Recall",c.recall],["Specificity",c.specificity],["F1",c.f1]].map(([name,value]) => `<div class="bar-row"><span>${name}</span><i><em style="width:${Number(value)*100}%"></em></i><b>${pct(value)}</b></div>`).join("")}<p class="muted">Majority baseline accuracy: ${pct(c.majority_baseline_accuracy)}</p></article></div>`;
  if (state.module === "regression") return `<div class="detail-grid"><article class="panel large"><div class="panel-top"><span class="tag">OBSERVED HOLDOUT</span><strong>${r.scored_rows} scored rows</strong></div><div class="compare"><div><span>MODEL MAE</span><b>${num(r.mae)}</b><small>usage units</small></div><div><span>MEAN BASELINE</span><b>${num(r.mean_baseline_mae)}</b><small>train mean</small></div><div><span>R²</span><b>${num(r.r2)}</b><small>variance explained</small></div></div><div class="mini-chart"><span style="height:${Math.min(100, r.mae / r.mean_baseline_mae * 100)}%"></span><span style="height:100%"></span></div><p class="callout">Missing targets are excluded from scoring: ${r.missing_test_targets_excluded}. Features are imputed using training-only medians.</p></article><article class="panel"><span class="tag">PREDICTION SAMPLE</span><h3>Actual vs predicted</h3><div class="table">${(summary.regression_predictions || []).slice(0,6).map((row) => `<div><span>${esc(row.customer_id)}</span><b>${num(row.actual_usage)}</b><span>→</span><b>${num(row.predicted_usage)}</b></div>`).join("")}</div></article></div>`;
  if (state.module === "clustering") return `<div class="detail-grid"><article class="panel large"><div class="panel-top"><span class="tag">SCALED K-MEANS</span><strong>k = ${k.k}</strong></div><div class="cluster-chart">${k.centers.map((center,index) => `<div class="cluster-node node-${index}" style="left:${18 + index*54}%;top:${35 + index*18}%"><b>${index}</b><span>${num(center[0])} usage · ${num(center[1])} tickets</span></div>`).join("")}</div><p class="callout">Z-score scaling prevents monthly usage from dominating support-ticket distance. Silhouette: ${num(k.silhouette)}.</p></article><article class="panel"><span class="tag">FILTERED POINTS</span><h3>${rows.length} of ${summary.analysis_rows.length} customers</h3><div class="table">${rows.slice(0,8).map((row) => `<div><span>${esc(row.customer_id)}</span><b>G${row.cluster}</b><span>${num(row.monthly_usage)}</span><small>${esc(row.plan)}</small></div>`).join("")}</div></article></div>`;
  return `<div class="detail-grid"><article class="panel large"><span class="tag">PIPELINE MAP</span><div class="pipeline"><span>CSV ingest</span><i>→</i><span>validate + clean</span><i>→</i><span>fit boundaries</span><i>→</i><span>evaluate</span></div><p class="callout">Five modules share one validated fixture, but each uses an appropriate DS protocol: stratified classification, continuous regression, descriptive EDA, and scaled unsupervised clustering.</p></article><article class="panel"><span class="tag">RUN CONTEXT</span><h3>Seeded, offline, inspectable</h3><dl><dt>Input rows</dt><dd>${q.raw_rows}</dd><dt>Fixture</dt><dd>synthetic CSV</dd><dt>Seed</dt><dd>${metrics.reproducibility.seed}</dd><dt>Methods</dt><dd>standard library</dd></dl></article></div>`;
}
function bindModule() { /* Module-specific controls are stateful filters rendered above. */ }
shell(); load();
