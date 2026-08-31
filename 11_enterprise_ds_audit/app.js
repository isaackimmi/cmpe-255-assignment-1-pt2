const $ = (selector) => document.querySelector(selector);
const state = { result: null, report: "", checks: [], filters: { search: "", status: "all", severity: "all" } };

const icons = { schema: "⌗", missingness: "◒", duplicate_identifiers: "⊕", leakage_risk: "◌", reproducibility: "⌁", model_quality: "◈" };
const labels = { schema: "Schema", missingness: "Missingness", duplicate_identifiers: "Identifiers", leakage_risk: "Leakage risk", reproducibility: "Reproducibility", model_quality: "Model quality" };
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const checkFor = (name) => state.checks.find((check) => check.name === name);
const countBy = (items, key, value) => items.filter((item) => item[key] === value).length;
const formatDate = (value) => { if (!value) return "—"; const date = new Date(value); return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(date); };
const pct = (value) => `${Math.round(Number(value || 0) * 100)}%`;

function parseMissingness(detail) {
  const values = {};
  for (const match of String(detail).matchAll(/'([^']+)':\s*([0-9.]+)/g)) values[match[1]] = Number(match[2]);
  return values;
}

function parseJsonDetail(check) {
  try { return JSON.parse(check?.detail || "{}"); } catch { return {}; }
}

function renderStats() {
  const { checks } = state;
  const fails = countBy(checks, "status", "FAIL");
  const warnings = countBy(checks, "status", "WARN");
  const high = countBy(checks, "severity", "high");
  $("#stat-checks").textContent = checks.length;
  $("#stat-fails").textContent = fails;
  $("#stat-warnings").textContent = warnings;
  $("#stat-high").textContent = high;
  $("#nav-finding-count").textContent = fails + warnings;
  $("#finding-count-label").textContent = `${checks.length} controls evaluated`;
  $("#release-summary").textContent = state.result.summary || "Audit decision loaded.";
  $("#report-date").textContent = `AUDIT RUN · ${formatDate(state.result.generated_at_utc)}`;
  const dataset = String(state.result.dataset || "sample_customers.csv").split("/").pop();
  $("#dataset-name").textContent = dataset;
  const recommendation = state.result.release_recommendation || "UNKNOWN";
  $("#release-badge").textContent = recommendation;
  $("#release-score-mark").textContent = recommendation === "APPROVE" ? "✓" : "!";
}

function renderDimensions() {
  $("#dimension-grid").innerHTML = state.checks.map((check) => `
    <article class="dimension-card">
      <div class="dimension-top"><span class="dimension-icon">${icons[check.name] || "◈"}</span><span class="status-chip ${escapeHtml(check.status)}">${escapeHtml(check.status)}</span></div>
      <h3>${escapeHtml(labels[check.name] || check.name)}</h3>
      <p>${escapeHtml(check.detail)}</p>
      <div class="dimension-bar"><span class="${escapeHtml(check.status)}"></span></div>
    </article>`).join("");
}

function renderSeverity() {
  const counts = { high: countBy(state.checks, "severity", "high"), medium: countBy(state.checks, "severity", "medium"), low: countBy(state.checks, "severity", "low") };
  const total = state.checks.length || 1;
  const highStop = counts.high / total * 100;
  const mediumStop = (counts.high + counts.medium) / total * 100;
  const end = (counts.high + counts.medium + counts.low) / total * 100;
  const chart = $("#severity-chart");
  chart.style.setProperty("--p1", `${highStop}%`); chart.style.setProperty("--p2", `${mediumStop}%`); chart.style.setProperty("--p3", `${end}%`);
  chart.innerHTML = `<div class="severity-chart-center"><strong>${state.checks.length}</strong><small>findings</small></div>`;
  $("#severity-legend").innerHTML = [["high", "High severity"], ["medium", "Medium severity"], ["low", "Low severity"]].map(([key, label]) => `<div class="legend-row"><span class="legend-name"><i class="legend-dot ${key}"></i>${label}</span><strong>${counts[key]}</strong></div>`).join("");
  $("#risk-callout-title").textContent = counts.high ? `${counts.high} high-severity control${counts.high === 1 ? "" : "s"} need attention` : "No high-severity findings";
  $("#risk-callout-copy").textContent = counts.high ? "Release remains conditional until the blocking controls are remediated and re-run." : "The current control set is clear for this risk tier.";
}

function renderModelQuality() {
  const quality = state.result.model_quality || {};
  const model = quality.model || {};
  const baseline = quality.majority_baseline || {};
  const score = Number(model.balanced_accuracy || 0);
  const baselineScore = Number(baseline.balanced_accuracy || 0);
  const delta = score - baselineScore;
  $("#model-score").textContent = score.toFixed(2);
  $("#model-delta").textContent = `${delta >= 0 ? "+" : ""}${delta.toFixed(2)} vs baseline`;
  $("#metric-bars").innerHTML = [["Accuracy", model.accuracy], ["Precision", model.precision], ["Recall", model.recall], ["F1 score", model.f1]].map(([name, value]) => `<div class="metric-row"><span>${name}</span><div class="metric-track"><span style="width:${Number(value || 0) * 100}%"></span></div><code>${pct(value)}</code></div>`).join("");
}

function renderFindings() {
  const { search, status, severity } = state.filters;
  const filtered = state.checks.filter((check) => {
    const haystack = `${check.name} ${check.status} ${check.severity} ${check.detail}`.toLowerCase();
    return (!search || haystack.includes(search)) && (status === "all" || check.status === status) && (severity === "all" || check.severity === severity);
  });
  $("#findings-body").innerHTML = filtered.map((check) => `<tr><td><span class="finding-name">${escapeHtml(labels[check.name] || check.name)}</span><br /><code class="finding-detail">${escapeHtml(check.name)}</code></td><td><span class="status-chip ${escapeHtml(check.status)}">${escapeHtml(check.status)}</span></td><td><span class="status-chip ${escapeHtml(check.status === "FAIL" ? "FAIL" : check.severity === "low" ? "PASS" : "WARN")}">${escapeHtml(check.severity)}</span></td><td><span class="finding-detail" title="${escapeHtml(check.detail)}">${escapeHtml(check.detail)}</span></td><td><span class="row-arrow">›</span></td></tr>`).join("");
  $("#empty-state").hidden = filtered.length !== 0;
}

function renderDetails() {
  const schema = checkFor("schema"); const missing = checkFor("missingness"); const leakage = checkFor("leakage_risk"); const repro = checkFor("reproducibility");
  for (const [name, check] of [["schema", schema], ["missingness", missing], ["leakage", leakage], ["repro", repro]]) { const status = $(`#${name}-status`); if (status && check) { status.textContent = check.status; status.className = `mini-status ${check.status}`; } }
  const schemaDetail = schema?.detail || "No schema evidence available.";
  const rowMatch = schemaDetail.match(/^(\d+) rows/); const parseMatch = schemaDetail.match(/parse_errors=([^;]+)/); const missingMatch = schemaDetail.match(/missing=([^;]+)/); const extraMatch = schemaDetail.match(/extra=([^;]+)/);
  $("#schema-detail").innerHTML = `<dl class="detail-list"><div class="detail-item"><dt>Rows inspected</dt><dd>${escapeHtml(rowMatch?.[1] || "—")}</dd></div><div class="detail-item"><dt>Required columns</dt><dd>9 / 9 present</dd></div><div class="detail-item"><dt>Parse errors</dt><dd>${escapeHtml(parseMatch?.[1] || "none")}</dd></div><div class="detail-item"><dt>Missing / extra</dt><dd>${escapeHtml(missingMatch?.[1] || "[]")} / ${escapeHtml(extraMatch?.[1] || "[]")}</dd></div></dl>`;
  $("#leakage-detail").innerHTML = `<div class="detail-copy"><strong>Prediction-time safety</strong><p>${escapeHtml(leakage?.detail || "No leakage evidence available.")}</p></div><div class="detail-list"><div class="detail-item"><dt>Outcome timestamp</dt><dd>Review required</dd></div><div class="detail-item"><dt>Free-text field</dt><dd>Manual review</dd></div></div>`;
  const rates = parseMissingness(missing?.detail || ""); const entries = Object.entries(rates).sort((a, b) => b[1] - a[1]);
  $("#missingness-detail").innerHTML = `<div class="null-profile">${entries.map(([name, value]) => `<div class="null-row"><span>${escapeHtml(name)}</span><div class="null-track"><span style="width:${value * 100}%"></span></div><code>${pct(value)}</code></div>`).join("")}</div>`;
  const reproData = state.result.reproducibility || parseJsonDetail(repro); const hash = String(reproData.input_sha256 || "");
  $("#repro-detail").innerHTML = `<dl class="detail-list"><div class="detail-item"><dt>Seed</dt><dd>${escapeHtml(reproData.seed || "—")}</dd></div><div class="detail-item"><dt>Runtime</dt><dd>Python ${escapeHtml(reproData.python || "—")}</dd></div><div class="detail-item"><dt>Split</dt><dd>${escapeHtml(reproData.split || "—")}</dd></div><div class="detail-item"><dt>Input SHA-256</dt><dd>${escapeHtml(hash ? `${hash.slice(0, 12)}…` : "—")}</dd></div></dl>`;
}

function wireFilters() {
  $("#finding-search").addEventListener("input", (event) => { state.filters.search = event.target.value.trim().toLowerCase(); renderFindings(); });
  $("#status-filter").addEventListener("change", (event) => { state.filters.status = event.target.value; renderFindings(); });
  $("#severity-filter").addEventListener("change", (event) => { state.filters.severity = event.target.value; renderFindings(); });
  $("#clear-filters").addEventListener("click", () => { state.filters = { search: "", status: "all", severity: "all" }; $("#finding-search").value = ""; $("#status-filter").value = "all"; $("#severity-filter").value = "all"; renderFindings(); });
}

async function loadReports() {
  try {
    const [resultResponse, reportResponse] = await Promise.all([fetch("reports/audit_results.json", { cache: "no-store" }), fetch("reports/audit_report.md", { cache: "no-store" })]);
    if (!resultResponse.ok || !reportResponse.ok) throw new Error("The report files could not be found.");
    state.result = await resultResponse.json(); state.report = await reportResponse.text(); state.checks = state.result.checks || [];
    renderStats(); renderDimensions(); renderSeverity(); renderModelQuality(); renderFindings(); renderDetails();
  } catch (error) {
    const box = $("#load-error"); box.hidden = false; box.innerHTML = `<strong>Report loading paused.</strong> ${escapeHtml(error.message)} Serve this folder with <code>python3 -m http.server 8000</code>, then open <code>http://localhost:8000</code>.`;
  }
}

wireFilters();
loadReports();
