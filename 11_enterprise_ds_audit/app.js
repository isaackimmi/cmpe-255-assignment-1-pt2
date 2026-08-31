const $ = (selector) => document.querySelector(selector);
const state = { result: null, checks: [], filters: { search: "", status: "all", severity: "all", category: "all" }, lastFocus: null };
const icons = { schema: "⌗", missingness: "◒", duplicate_identifiers: "⊕", domain_validity: "⌖", leakage_risk: "◌", reproducibility: "⌁", model_quality: "◈" };
const labels = { schema: "Schema", missingness: "Missingness", duplicate_identifiers: "Identifiers", domain_validity: "Domain validity", leakage_risk: "Leakage risk", reproducibility: "Reproducibility", model_quality: "Model quality" };
const categoryLabels = { schema: "Schema", completeness: "Completeness", data_integrity: "Data integrity", domain: "Domain", governance: "Governance", model_quality: "Model quality" };
const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const safeStatus = (status) => ["FAIL", "PASS", "WARN", "INCONCLUSIVE"].includes(status) ? status : "INCONCLUSIVE";
const checkFor = (name) => state.checks.find((check) => check.name === name);
const countBy = (items, key, value) => items.filter((item) => item[key] === value).length;
const formatDate = (value) => { if (!value) return "—"; const parsed = new Date(value); return Number.isNaN(parsed.valueOf()) ? value : new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(parsed); };
const pct = (value) => Math.round(Number(value || 0) * 100) + "%";

function renderStructuredEvidence(value, depth) {
  depth = depth || 0;
  if (value === null || value === undefined || value === "") return '<span class="evidence-null">—</span>';
  if (typeof value !== "object") return "<span>" + escapeHtml(value) + "</span>";
  if (depth > 4) return "<code>" + escapeHtml(JSON.stringify(value)) + "</code>";
  if (Array.isArray(value)) {
    if (!value.length) return '<span class="evidence-null">none</span>';
    return '<div class="evidence-array">' + value.map((item) => '<div class="evidence-array-item">' + renderStructuredEvidence(item, depth + 1) + "</div>").join("") + "</div>";
  }
  const entries = Object.entries(value);
  if (!entries.length) return '<span class="evidence-null">none</span>';
  return '<dl class="structured-list">' + entries.map(([key, item]) => '<div class="structured-item"><dt>' + escapeHtml(key) + "</dt><dd>" + renderStructuredEvidence(item, depth + 1) + "</dd></div>").join("") + "</dl>";
}

function decisionContext() {
  const decision = state.result.decision || {};
  const blocking = decision.blocking_findings || [];
  const advisory = decision.advisory_findings || decision.warning_findings || [];
  const names = (items) => items.map((item) => item.name || item).join(", ") || "none";
  return '<div class="drawer-decision"><strong>' + escapeHtml((state.result.decision_state || "UNKNOWN") + " · " + (state.result.release_recommendation || "UNKNOWN")) + "</strong><p>" + escapeHtml(decision.text || "No decision explanation available.") + '</p><div class="decision-columns"><div><span>Blocking</span><b>' + blocking.length + "</b><small>" + escapeHtml(names(blocking)) + '</small></div><div><span>Advisory</span><b>' + advisory.length + "</b><small>" + escapeHtml(names(advisory)) + "</small></div></div></div>";
}

function renderStats() {
  const checks = state.checks;
  const decision = state.result.decision || {};
  const blocking = decision.blocking_findings || [];
  const advisory = decision.advisory_findings || decision.warning_findings || [];
  const high = checks.filter((check) => check.severity === "high" && check.status !== "PASS").length;
  $("#stat-checks").textContent = checks.length;
  $("#stat-fails").textContent = blocking.length;
  $("#stat-warnings").textContent = advisory.length;
  $("#stat-high").textContent = high;
  $("#nav-finding-count").textContent = blocking.length + advisory.length;
  $("#finding-count-label").textContent = checks.length + " controls evaluated";
  $("#release-summary").textContent = state.result.summary || "Audit decision loaded.";
  $("#report-date").textContent = "AUDIT RUN · " + formatDate(state.result.generated_at_utc);
  $("#dataset-name").textContent = String(state.result.dataset || "sample_customers.csv").split("/").pop();
  const recommendation = state.result.release_recommendation || "UNKNOWN";
  $("#release-badge").textContent = recommendation;
  $("#release-score-mark").textContent = recommendation === "APPROVE" ? "✓" : "!";
}

function renderDimensions() {
  $("#dimension-grid").innerHTML = state.checks.map((check) => '<article class="dimension-card"><div class="dimension-top"><span class="dimension-icon">' + (icons[check.name] || "◈") + '</span><span class="status-chip ' + safeStatus(check.status) + '">' + escapeHtml(check.status) + "</span></div><h3>" + escapeHtml(labels[check.name] || check.name) + "</h3><p>" + escapeHtml(check.detail) + '</p><div class="dimension-bar"><span class="' + safeStatus(check.status) + '"></span></div></article>').join("");
}

function renderSeverity() {
  const counts = { high: countBy(state.checks, "severity", "high"), medium: countBy(state.checks, "severity", "medium"), low: countBy(state.checks, "severity", "low") };
  const total = state.checks.length || 1;
  const chart = $("#severity-chart");
  chart.style.setProperty("--p1", counts.high / total * 100 + "%");
  chart.style.setProperty("--p2", (counts.high + counts.medium) / total * 100 + "%");
  chart.style.setProperty("--p3", (counts.high + counts.medium + counts.low) / total * 100 + "%");
  chart.innerHTML = '<div class="severity-chart-center"><strong>' + state.checks.length + '</strong><small>controls</small></div>';
  $("#severity-legend").innerHTML = [["high", "High severity"], ["medium", "Medium severity"], ["low", "Low severity"]].map(([key, label]) => '<div class="legend-row"><span class="legend-name"><i class="legend-dot ' + key + '"></i>' + label + "</span><strong>" + counts[key] + "</strong></div>").join("");
  const attention = state.checks.filter((check) => check.severity === "high" && check.status !== "PASS").length;
  $("#risk-callout-title").textContent = attention ? attention + " high-severity control" + (attention === 1 ? "" : "s") + " need attention" : "No high-severity findings";
  $("#risk-callout-copy").textContent = attention ? "Release remains gated until the blocking controls are remediated and re-run." : "The current control set is clear for this risk tier.";
}

function renderModelQuality() {
  const quality = state.result.model_quality || {};
  const model = quality.model || {};
  const baseline = quality.majority_baseline || {};
  if (!["PASS", "WARN"].includes(quality.status)) {
    $("#model-score").textContent = "—";
    $("#model-delta").textContent = quality.status || "INCONCLUSIVE";
    $("#metric-bars").innerHTML = '<p class="panel-note">' + escapeHtml(quality.reason || "Model evaluation was not completed.") + "</p>" + renderStructuredEvidence({ feature_manifest: quality.feature_manifest, model_feature_manifest: quality.model_feature_manifest, excluded_rows: quality.excluded_rows });
    return;
  }
  const score = Number(model.balanced_accuracy || 0);
  const baselineScore = Number(baseline.balanced_accuracy || 0);
  $("#model-score").textContent = score.toFixed(2);
  $("#model-delta").textContent = (score >= baselineScore ? "+" : "") + (score - baselineScore).toFixed(2) + " vs baseline";
  $("#metric-bars").innerHTML = [["Accuracy", model.accuracy], ["Precision", model.precision], ["Recall", model.recall], ["F1 score", model.f1]].map(([name, value]) => '<div class="metric-row"><span>' + name + '</span><div class="metric-track"><span style="width:' + Math.max(0, Math.min(100, Number(value || 0) * 100)) + '%"></span></div><code>' + pct(value) + "</code></div>").join("") + '<details class="model-evidence"><summary>Open model evidence</summary>' + renderStructuredEvidence({ ci95: quality.balanced_accuracy_ci95, threshold: quality.operating_threshold, windows: quality.temporal_windows, confusion_matrix: model.confusion_matrix, class_support: model.class_support, pipeline: quality.model_configuration, feature_manifest: quality.feature_manifest }) + "</details>";
}

function renderFindings() {
  const filters = state.filters;
  const filtered = state.checks.filter((check) => {
    const haystack = (check.name + " " + (check.category || "") + " " + check.status + " " + check.severity + " " + check.detail + " " + JSON.stringify(check.evidence || {})).toLowerCase();
    return (!filters.search || haystack.includes(filters.search)) && (filters.status === "all" || check.status === filters.status) && (filters.severity === "all" || check.severity === filters.severity) && (filters.category === "all" || (check.category || "governance") === filters.category);
  });
  $("#findings-body").innerHTML = filtered.map((check) => '<tr><th scope="row"><span class="finding-name">' + escapeHtml(labels[check.name] || check.name) + '</span><br /><code class="finding-detail">' + escapeHtml(check.name) + '</code></th><td><span class="status-chip ' + safeStatus(check.status) + '">' + escapeHtml(check.status) + '</span></td><td><span class="severity-chip ' + escapeHtml(check.severity || "medium") + '">' + escapeHtml(check.severity || "medium") + '</span></td><td><span class="finding-detail" title="' + escapeHtml(check.detail) + '">' + escapeHtml(check.detail) + '</span></td><td><button class="row-arrow finding-open" type="button" data-open-check="' + escapeHtml(check.name) + '" aria-label="Open evidence for ' + escapeHtml(labels[check.name] || check.name) + '">›</button></td></tr>').join("");
  $("#empty-state").hidden = filtered.length !== 0;
}

function setPanelStatus(id, check) {
  const status = $("#" + id + "-status");
  if (status && check) { status.textContent = check.status; status.className = "mini-status " + safeStatus(check.status); }
}

function renderDetails() {
  const schema = checkFor("schema"); const missing = checkFor("missingness"); const duplicate = checkFor("duplicate_identifiers"); const domain = checkFor("domain_validity"); const leakage = checkFor("leakage_risk"); const model = checkFor("model_quality"); const repro = checkFor("reproducibility");
  [["schema", schema], ["missingness", missing], ["leakage", leakage], ["repro", repro]].forEach(([name, check]) => setPanelStatus(name, check));
  const schemaEvidence = schema && schema.evidence || {};
  $("#schema-detail").innerHTML = renderStructuredEvidence({ rows_inspected: schemaEvidence.rows_inspected, required_columns: ((schemaEvidence.required_columns || []).length - (schemaEvidence.missing_columns || []).length) + " / " + ((schemaEvidence.required_columns || []).length || 9) + " present", row_error_count: schemaEvidence.row_error_count, missing_columns: schemaEvidence.missing_columns, extra_columns: schemaEvidence.extra_columns, row_errors: schemaEvidence.row_errors });
  const leakageEvidence = leakage && leakage.evidence || {};
  $("#leakage-detail").innerHTML = renderStructuredEvidence({ prediction_time_column: leakageEvidence.prediction_time_column, label_column: leakageEvidence.label_column, feature_manifest: leakageEvidence.feature_manifest, offending_features: leakageEvidence.offending_features, excluded_suspicious_columns: leakageEvidence.excluded_suspicious_columns });
  const rates = missing && missing.evidence && missing.evidence.null_rates || {};
  const entries = Object.entries(rates).sort((a, b) => b[1] - a[1]);
  $("#missingness-detail").innerHTML = entries.length ? '<div class="null-profile">' + entries.map(([name, value]) => '<div class="null-row"><span>' + escapeHtml(name) + '</span><div class="null-track"><span style="width:' + Math.max(0, Math.min(100, value * 100)) + '%"></span></div><code>' + pct(value) + "</code></div>").join("") + "</div>" : '<p class="detail-copy">No missingness evidence available.</p>';
  const reproData = state.result.reproducibility || repro && repro.evidence || {};
  $("#repro-detail").innerHTML = renderStructuredEvidence({ as_of_date: state.result.config && state.result.config.as_of_date || domain && domain.evidence && domain.evidence.as_of_date, policy_version: reproData.policy_version, seed: reproData.seed, runtime: reproData.python, rerun_match: reproData.rerun_match, input_sha256: reproData.input_sha256, canonical_sha256: reproData.canonical_result_sha256, independent_rerun_sha256: reproData.rerun_canonical_result_sha256, model_configuration_sha256: reproData.model_configuration_sha256, runner_sha256: reproData.runner_sha256 });
  $("#evidence-caption").textContent = [duplicate, domain, model].filter(Boolean).map((check) => (labels[check.name] || check.name) + ": " + check.status).join(" · ");
}

function openFinding(name, trigger) {
  const check = checkFor(name);
  if (!check) return;
  state.lastFocus = trigger || document.activeElement;
  $("#finding-drawer-title").textContent = labels[check.name] || check.name;
  $("#finding-drawer-meta").innerHTML = '<span class="status-chip ' + safeStatus(check.status) + '">' + escapeHtml(check.status) + '</span><span class="severity-chip ' + escapeHtml(check.severity || "medium") + '">' + escapeHtml(check.severity || "medium") + '</span><span class="category-chip">' + escapeHtml(categoryLabels[check.category] || check.category || "Governance") + "</span>";
  $("#finding-drawer-detail").textContent = check.detail || "No detail supplied.";
  $("#finding-drawer-evidence").innerHTML = renderStructuredEvidence(check.evidence || {});
  $("#finding-drawer-decision").innerHTML = decisionContext();
  const drawer = $("#finding-drawer"); drawer.hidden = false; drawer.setAttribute("aria-hidden", "false"); $("#finding-drawer-close").focus();
}

function closeFinding() {
  const drawer = $("#finding-drawer"); drawer.hidden = true; drawer.setAttribute("aria-hidden", "true");
  if (state.lastFocus && typeof state.lastFocus.focus === "function") state.lastFocus.focus();
}

function wireFilters() {
  $("#finding-search").addEventListener("input", (event) => { state.filters.search = event.target.value.trim().toLowerCase(); renderFindings(); });
  $("#status-filter").addEventListener("change", (event) => { state.filters.status = event.target.value; renderFindings(); });
  $("#severity-filter").addEventListener("change", (event) => { state.filters.severity = event.target.value; renderFindings(); });
  $("#category-filter").addEventListener("change", (event) => { state.filters.category = event.target.value; renderFindings(); });
  $("#clear-filters").addEventListener("click", () => { state.filters = { search: "", status: "all", severity: "all", category: "all" }; $("#finding-search").value = ""; $("#status-filter").value = "all"; $("#severity-filter").value = "all"; $("#category-filter").value = "all"; renderFindings(); });
  $("#findings-body").addEventListener("click", (event) => { const trigger = event.target.closest("[data-open-check]"); if (trigger) openFinding(trigger.dataset.openCheck, trigger); });
  $("#finding-drawer-close").addEventListener("click", closeFinding);
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !$("#finding-drawer").hidden) closeFinding(); });
}

async function loadReports() {
  try {
    const response = await fetch("reports/audit_results.json", { cache: "no-store" });
    if (!response.ok) throw new Error("The machine-readable audit report could not be found.");
    state.result = await response.json(); state.checks = Array.isArray(state.result.checks) ? state.result.checks : [];
    renderStats(); renderDimensions(); renderSeverity(); renderModelQuality(); renderFindings(); renderDetails();
  } catch (error) {
    const box = $("#load-error"); box.hidden = false; box.innerHTML = "<strong>Report loading paused.</strong> " + escapeHtml(error.message) + " Serve this folder with <code>python3 -m http.server 8000</code>, then open <code>http://localhost:8000</code>.";
  }
}

wireFilters();
loadReports();
