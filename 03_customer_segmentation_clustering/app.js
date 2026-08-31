const state = {
  filter: "all",
  feature: "spend_score",
  xFeature: "spend_score",
  yFeature: "annual_income_k",
  projection: "features",
  selectedCustomer: null,
  explorerRows: []
};
const featureLabels = {
  annual_income_k: "Annual income",
  spend_score: "Spend score",
  purchase_frequency: "Purchase frequency",
  avg_order_value: "Average order value"
};
const palette = ["#2b8c86", "#ed8e5b", "#b99b32", "#6575b8", "#9a5d87", "#59806b", "#ba6548"];
const phaseContent = {
  business: ["01 / BUSINESS UNDERSTANDING", "Turn cluster output into a decision surface.", "Identify actionable customer groups for differentiated offers while keeping the experiment’s assumptions explicit.", "A segment is a conversation starter, not a verdict about a person."],
  data: ["02 / DATA UNDERSTANDING", "Start with a small, legible customer universe.", "The run creates 120 synthetic retail customers across three intentionally interpretable prototypes and four numeric behavioral/value features.", "The data is generated, bounded, and reproducible — not observed customer behavior."],
  prep: ["03 / DATA PREPARATION", "Shape the signals before measuring distance.", "Impossible synthetic values are clipped; the run compares StandardScaler with an optional log1p transform for income and average order value.", "Preprocessing changes what ‘similar’ means, so it belongs in the story."],
  model: ["04 / MODELING", "Let K-Means test a small range of shapes.", "K-Means is fit for the predeclared k=2 through 7 candidates with 25 initializations. The selected assignments are exported with the raw feature values.", "The cluster IDs are labels, not rankings — their names here are interpretive aids."],
  evaluate: ["05 / EVALUATION", "Check signal beyond one fitted sample.", "Candidates are compared with repeated held-out splits; partition stability is summarized with adjusted Rand index. Full-sample metrics remain descriptive diagnostics.", "Synthetic-data validation is exploratory and does not establish campaign lift, future performance, fairness, or causality."],
  deploy: ["06 / DEPLOYMENT / USE", "Carry the assignment into a careful next step.", "Use the exported segment table as a starting point for campaign hypotheses, then validate on real longitudinal transactions and monitor drift.", "Never use these teaching segments to deny service or infer sensitive traits."]
};

const $ = (selector) => document.querySelector(selector);
const formatNumber = (value, digits = 2) => Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
const formatFeature = (feature, value) => feature === "purchase_frequency" ? `${formatNumber(value, 1)} / yr` : feature === "annual_income_k" ? `$${formatNumber(value, 0)}k` : `$${formatNumber(value, 0)}`;
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[character]));

function parseCsv(text) {
  const trimmed = text.trim();
  if (!trimmed) return [];
  const [header, ...lines] = trimmed.split(/\r?\n/);
  const keys = header.split(",");
  return lines.filter(Boolean).map((line) => {
    const values = line.split(",");
    return Object.fromEntries(keys.map((key, index) => {
      const raw = values[index] ?? "";
      const number = Number(raw);
      return [key, raw !== "" && Number.isFinite(number) ? number : raw];
    }));
  });
}

function assertFrame(frame, expectedColumns, name, numericColumns = []) {
  const columns = frame.length ? Object.keys(frame[0]) : [];
  if (JSON.stringify(columns) !== JSON.stringify(expectedColumns)) throw new Error(`${name} schema mismatch.`);
  if (!frame.length) throw new Error(`${name} is empty.`);
  frame.forEach((row) => numericColumns.forEach((column) => {
    if (!Number.isFinite(Number(row[column]))) throw new Error(`${name} contains an invalid ${column}.`);
  }));
}

function profileName(means, profiles) {
  const frequencyLeader = profiles.reduce((best, profile) => profile.means.purchase_frequency > best.means.purchase_frequency ? profile : best, profiles[0]);
  const aovLeader = profiles.reduce((best, profile) => profile.means.avg_order_value > best.means.avg_order_value ? profile : best, profiles[0]);
  if (means.cluster === frequencyLeader.means.cluster) return ["High-frequency heuristic", "Frequent in this toy sample", "Hypothesis only · test retention messaging"];
  if (means.cluster === aovLeader.means.cluster) return ["High-order-value heuristic", "Larger baskets in this toy sample", "Hypothesis only · test value messaging"];
  return ["Lower-frequency heuristic", "Lower observed frequency in this toy sample", "Hypothesis only · validate a growth path"];
}

function buildProfiles(assignments) {
  const byCluster = new Map();
  assignments.forEach((row) => {
    if (!byCluster.has(row.cluster)) byCluster.set(row.cluster, []);
    byCluster.get(row.cluster).push(row);
  });
  const profiles = [...byCluster.entries()].map(([cluster, rows]) => {
    const means = { cluster };
    Object.keys(featureLabels).forEach((feature) => { means[feature] = rows.reduce((sum, row) => sum + row[feature], 0) / rows.length; });
    return { cluster, rows, count: rows.length, means };
  });
  profiles.forEach((profile) => { [profile.name, profile.subtitle, profile.guidance] = profileName(profile.means, profiles); });
  profiles.sort((left, right) => left.means.avg_order_value - right.means.avg_order_value);
  return profiles;
}

function visibleExplorerRows() {
  return state.filter === "all" ? state.explorerRows : state.explorerRows.filter((row) => String(row.cluster) === state.filter);
}

function renderMetrics(summary) {
  $("#hero-k").textContent = summary.selected_k;
  const prepLabel = summary.selected_preprocessing === "log1p" ? "log1p + StandardScaler" : "StandardScaler";
  $("#selected-model").textContent = `K-Means · k=${summary.selected_k}`;
  $("#run-size").textContent = `${prepLabel} · ${summary.n_customers} synthetic customers`;
  $("#silhouette").textContent = formatNumber(summary.validation.silhouette_mean, 4);
  $("#silhouette-note").textContent = `held-out mean ± ${formatNumber(summary.validation.silhouette_std, 4)}`;
  $("#stability").textContent = formatNumber(summary.validation.stability_ari_mean, 4);
  $("#stability-note").textContent = `ARI range ≥ ${formatNumber(summary.validation.stability_ari_min, 4)}`;
  $("#fit-silhouette").textContent = formatNumber(summary.fit_metrics.silhouette, 4);
  $("#fit-note").textContent = "full-sample descriptive only";
  $("#profile-heading").textContent = `${summary.selected_k} heuristic profiles, one useful starting point.`;
}

function renderProfiles(profiles) {
  const visible = state.filter === "all" ? profiles : profiles.filter((profile) => String(profile.cluster) === state.filter);
  if (!visible.length) { $("#profile-grid").innerHTML = '<div class="loading-card">No profiles match this filter.</div>'; return; }
  const maxValue = Math.max(...profiles.map((profile) => profile.means[state.feature]));
  $("#profile-grid").innerHTML = visible.map((profile, index) => {
    const accent = index % 3 === 1 ? "accent-orange" : index % 3 === 2 ? "accent-yellow" : "";
    const share = Math.round((profile.count / profiles.reduce((sum, item) => sum + item.count, 0)) * 100);
    const bar = Math.max(7, Math.round((profile.means[state.feature] / maxValue) * 100));
    return `<article class="profile-card ${accent}">
      <div class="profile-top"><div><span class="segment-index">SEGMENT ${profile.cluster}</span><h3>${escapeHtml(profile.name)}</h3><p class="profile-subtitle">${escapeHtml(profile.subtitle)}</p></div><div class="count-box"><strong>${profile.count}</strong><small>${share}% of sample</small></div></div>
      <div class="profile-stat"><div class="stat-label"><span>${featureLabels[state.feature]}</span><span>${formatFeature(state.feature, profile.means[state.feature])}</span></div><div class="bar-track"><div class="bar-fill" style="width:${bar}%"></div></div></div>
      <div class="stat-list"><div><span>Income</span><strong>${formatFeature("annual_income_k", profile.means.annual_income_k)}</strong></div><div><span>Spend score</span><strong>${formatNumber(profile.means.spend_score, 1)}</strong></div><div><span>Frequency</span><strong>${formatFeature("purchase_frequency", profile.means.purchase_frequency)}</strong></div><div><span>Avg order</span><strong>${formatFeature("avg_order_value", profile.means.avg_order_value)}</strong></div></div>
      <div class="profile-foot">${escapeHtml(profile.guidance)}</div>
    </article>`;
  }).join("");
}

function selectCustomer(customerId) {
  state.selectedCustomer = customerId;
  document.querySelectorAll("#explorer-canvas circle[data-customer]").forEach((point) => point.classList.toggle("is-selected", point.dataset.customer === customerId));
  const row = state.explorerRows.find((item) => item.customer_id === customerId);
  renderCustomerDetails(row);
}

function renderCustomerDetails(row) {
  const target = $("#customer-detail");
  if (!row) { target.innerHTML = '<p class="detail-empty">Select a point to inspect one customer record.</p>'; return; }
  const confidence = Number(row.assignment_confidence);
  target.innerHTML = `<div class="detail-kicker">POINT INSPECTOR</div>
    <div class="detail-title"><div><strong>${escapeHtml(row.customer_id)}</strong><span>Segment ${row.cluster}</span></div><span class="uncertainty-pill ${escapeHtml(row.uncertainty_label)}">${escapeHtml(row.uncertainty_label)} assignment</span></div>
    <p class="detail-copy">A raw synthetic customer record with a geometry-based assignment diagnostic. This label is not a probability or a behavioral truth.</p>
    <div class="detail-grid">${Object.keys(featureLabels).map((feature) => `<div><span>${featureLabels[feature]}</span><strong>${formatFeature(feature, row[feature])}</strong></div>`).join("")}</div>
    <div class="detail-diagnostics"><div><span>Geometry confidence proxy</span><strong>${formatNumber(confidence, 3)}</strong></div><div><span>Nearest-centroid distance</span><strong>${formatNumber(row.centroid_distance, 3)} units</strong></div><div><span>Runner-up margin</span><strong>${formatNumber(row.assignment_margin, 3)} units</strong></div></div>`;
}

function renderExplorer() {
  const rows = visibleExplorerRows();
  const mode = state.projection;
  const xKey = mode === "pca" ? "pca_x" : state.xFeature;
  const yKey = mode === "pca" ? "pca_y" : state.yFeature;
  const xLabel = mode === "pca" ? "PC1" : featureLabels[xKey];
  const yLabel = mode === "pca" ? "PC2" : featureLabels[yKey];
  $("#x-axis-label").textContent = xLabel; $("#y-axis-label").textContent = yLabel;
  $("#projection-note").textContent = mode === "pca" ? "PCA projection only · two axes summarize the four fitted dimensions" : "Raw feature view · points are placed on the selected original features";
  $("#explorer-count").textContent = `${rows.length} of ${state.explorerRows.length} points shown`;
  if (!rows.length) { $("#explorer-canvas").innerHTML = '<div class="loading-card">No customers match this segment filter.</div>'; renderCustomerDetails(null); return; }
  const width = 760; const height = 430; const pad = { left: 64, right: 25, top: 25, bottom: 52 };
  const extent = (key) => { const values = rows.map((row) => Number(row[key])); const min = Math.min(...values); const max = Math.max(...values); const spread = Math.max(max - min, 1); return [min - spread * .08, max + spread * .08]; };
  const xDomain = extent(xKey); const yDomain = extent(yKey);
  const sx = (value) => pad.left + ((Number(value) - xDomain[0]) / (xDomain[1] - xDomain[0])) * (width - pad.left - pad.right);
  const sy = (value) => height - pad.bottom - ((Number(value) - yDomain[0]) / (yDomain[1] - yDomain[0])) * (height - pad.top - pad.bottom);
  const xTicks = [0, .5, 1].map((fraction) => ({ x: pad.left + fraction * (width - pad.left - pad.right), value: xDomain[0] + fraction * (xDomain[1] - xDomain[0]) }));
  const yTicks = [0, .5, 1].map((fraction) => ({ y: height - pad.bottom - fraction * (height - pad.top - pad.bottom), value: yDomain[0] + fraction * (yDomain[1] - yDomain[0]) }));
  const grid = `${xTicks.map((tick) => `<line class="chart-grid" x1="${tick.x}" x2="${tick.x}" y1="${pad.top}" y2="${height - pad.bottom}"/><text class="chart-tick" x="${tick.x}" y="${height - pad.bottom + 24}" text-anchor="middle">${formatNumber(tick.value, 1)}</text>`).join("")}${yTicks.map((tick) => `<line class="chart-grid" x1="${pad.left}" x2="${width - pad.right}" y1="${tick.y}" y2="${tick.y}"/><text class="chart-tick" x="${pad.left - 12}" y="${tick.y + 4}" text-anchor="end">${formatNumber(tick.value, 1)}</text>`).join("")}`;
  const points = rows.map((row) => `<circle class="explorer-point ${row.customer_id === state.selectedCustomer ? "is-selected" : ""} ${row.uncertainty_label}" data-customer="${escapeHtml(row.customer_id)}" cx="${sx(row[xKey])}" cy="${sy(row[yKey])}" r="6" fill="${palette[Number(row.cluster) % palette.length]}" role="button" tabindex="0" aria-label="${escapeHtml(row.customer_id)}, segment ${row.cluster}, ${escapeHtml(row.uncertainty_label)} assignment"/>`).join("");
  $("#explorer-canvas").innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Interactive customer segmentation scatter plot">${grid}<line class="chart-axis" x1="${pad.left}" x2="${width - pad.right}" y1="${height - pad.bottom}" y2="${height - pad.bottom}"/><line class="chart-axis" x1="${pad.left}" x2="${pad.left}" y1="${pad.top}" y2="${height - pad.bottom}"/><text class="chart-axis-label" x="${(pad.left + width - pad.right) / 2}" y="${height - 10}" text-anchor="middle">${xLabel}</text><text class="chart-axis-label" transform="translate(17 ${(pad.top + height - pad.bottom) / 2}) rotate(-90)" text-anchor="middle">${yLabel}</text>${points}</svg>`;
  document.querySelectorAll("#explorer-canvas circle[data-customer]").forEach((point) => { point.addEventListener("click", () => selectCustomer(point.dataset.customer)); point.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectCustomer(point.dataset.customer); } }); });
  if (!state.selectedCustomer || !rows.some((row) => row.customer_id === state.selectedCustomer)) state.selectedCustomer = rows[0].customer_id;
  selectCustomer(state.selectedCustomer);
}

function renderFilters(profiles) {
  $("#segment-filters").innerHTML = profiles.map((profile) => `<button class="filter-button" data-filter="${profile.cluster}">Segment ${profile.cluster}</button>`).join("");
  document.querySelectorAll(".filter-button").forEach((button) => button.addEventListener("click", () => { state.filter = button.dataset.filter; document.querySelectorAll(".filter-button").forEach((item) => item.classList.toggle("is-active", item.dataset.filter === state.filter)); renderProfiles(profiles); renderExplorer(); }));
}

function renderScores(scores, selectedK, selectedPreprocessing) {
  $("#score-body").innerHTML = scores.map((row) => `<tr class="${Number(row.k) === Number(selectedK) && row.preprocessing === selectedPreprocessing ? "selected" : ""}"><td>${row.preprocessing === "log1p" ? "log1p" : "standard"}</td><td>${row.k}</td><td>${formatNumber(row.silhouette_mean, 4)} ± ${formatNumber(row.silhouette_std, 4)}</td><td>${formatNumber(row.stability_ari_mean, 4)}</td></tr>`).join("");
}

async function sha256Hex(buffer) { const digest = await crypto.subtle.digest("SHA-256", buffer); return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join(""); }
function parseJson(buffer) { return JSON.parse(new TextDecoder().decode(buffer)); }

async function validateDashboardArtifacts({ summary, baselineText, log1pText, validationText, assignmentsText, explorerText, manifest, hashes }) {
  const expectedFeatures = summary.features || [];
  const scoreColumns = ["k", "silhouette", "calinski_harabasz", "davies_bouldin"];
  const validationColumns = ["preprocessing", "k", "validation_repeats", "train_fraction", "silhouette_mean", "silhouette_std", "calinski_harabasz_mean", "calinski_harabasz_std", "davies_bouldin_mean", "davies_bouldin_std", "stability_ari_mean", "stability_ari_std", "stability_ari_min"];
  const assignmentColumns = [...expectedFeatures, "cluster"];
  const explorerColumns = ["customer_id", ...expectedFeatures, "cluster", "pca_x", "pca_y", "centroid_distance", "assignment_margin", "assignment_confidence", "uncertainty_label"];
  const baseline = parseCsv(baselineText); const log1p = parseCsv(log1pText); const validation = parseCsv(validationText); const assignments = parseCsv(assignmentsText); const explorer = parseCsv(explorerText);
  assertFrame(baseline, scoreColumns, "baseline scores", scoreColumns); assertFrame(log1p, scoreColumns, "log1p scores", scoreColumns); assertFrame(validation, validationColumns, "validation scores", validationColumns.slice(1)); assertFrame(assignments, assignmentColumns, "assignments", expectedFeatures.concat(["cluster"])); assertFrame(explorer, explorerColumns, "explorer points", expectedFeatures.concat(["cluster", "pca_x", "pca_y", "centroid_distance", "assignment_margin", "assignment_confidence"]));
  const candidateK = [2, 3, 4, 5, 6, 7];
  if (manifest.n_customers !== summary.n_customers || manifest.selected_k !== summary.selected_k || manifest.selected_preprocessing !== summary.selected_preprocessing || JSON.stringify(manifest.features) !== JSON.stringify(expectedFeatures) || assignments.length !== Number(summary.n_customers) || explorer.length !== assignments.length || baseline.length !== candidateK.length || log1p.length !== candidateK.length || validation.length !== candidateK.length * 2) throw new Error("Artifact metadata, schema, or row-count consistency check failed.");
  if (JSON.stringify(baseline.map((row) => Number(row.k))) !== JSON.stringify(candidateK) || JSON.stringify(log1p.map((row) => Number(row.k))) !== JSON.stringify(candidateK)) throw new Error("Score tables do not contain the predeclared candidate k values.");
  const validationKeys = validation.map((row) => `${row.preprocessing}:${Number(row.k)}`).sort();
  const expectedValidationKeys = ["standard", "log1p"].flatMap((variant) => candidateK.map((k) => `${variant}:${k}`)).sort();
  if (JSON.stringify(validationKeys) !== JSON.stringify(expectedValidationKeys)) throw new Error("Validation scores do not contain the complete preprocessing × k matrix.");
  const clusters = [...new Set(assignments.map((row) => Number(row.cluster)))].sort((a, b) => a - b);
  if (JSON.stringify(clusters) !== JSON.stringify(Array.from({ length: Number(summary.selected_k) }, (_, index) => index))) throw new Error("Assignment cluster labels are inconsistent.");
  explorer.forEach((row, index) => { if (row.customer_id !== `C${String(index + 1).padStart(3, "0")}` || !["clear", "moderate", "ambiguous"].includes(row.uncertainty_label)) throw new Error("Explorer point identifiers or uncertainty labels are invalid."); });
  if (!explorer.every((row, index) => Number(row.cluster) === Number(assignments[index].cluster))) throw new Error("Explorer clusters disagree with assignments.");
  const selectedRows = validation.filter((row) => row.preprocessing === summary.selected_preprocessing && Number(row.k) === Number(summary.selected_k));
  if (selectedRows.length !== 1 || !Number.isFinite(Number(selectedRows[0].silhouette_mean)) || Math.abs(Number(selectedRows[0].silhouette_mean) - Number(summary.validation.silhouette_mean)) > 1e-9 || Math.abs(Number(selectedRows[0].stability_ari_mean) - Number(summary.validation.stability_ari_mean)) > 1e-9) throw new Error("Selected validation result is missing or invalid.");
  const expectedNames = ["summary.json", "baseline_scores.csv", "log1p_scores.csv", "validation_scores.csv", "customer_segments.csv", "explorer_points.csv", "segmentation.png"];
  if (manifest.manifest_version !== 2 || JSON.stringify(Object.keys(manifest.hashes || {}).sort()) !== JSON.stringify([...expectedNames].sort())) throw new Error("Manifest version or hash set is incomplete.");
  expectedNames.forEach((name) => { if (!hashes[name] || hashes[name] !== manifest.hashes[name]) throw new Error(`Manifest hash mismatch: ${name}`); });
  return { assignments, explorer, validation };
}

function setupPhases() {
  document.querySelectorAll(".phase-button").forEach((button) => button.addEventListener("click", () => { const content = phaseContent[button.dataset.phase]; document.querySelectorAll(".phase-button").forEach((item) => { item.classList.toggle("is-active", item === button); item.setAttribute("aria-selected", item === button ? "true" : "false"); }); $("#phase-number").textContent = content[0]; $("#phase-title").textContent = content[1]; $("#phase-description").textContent = content[2]; $("#phase-callout").textContent = content[3]; }));
}

async function loadDashboard() {
  try {
    const [summaryResponse, baselineResponse, log1pResponse, validationResponse, assignmentsResponse, explorerResponse, manifestResponse, plotResponse] = await Promise.all([fetch("artifacts/summary.json"), fetch("artifacts/baseline_scores.csv"), fetch("artifacts/log1p_scores.csv"), fetch("artifacts/validation_scores.csv"), fetch("artifacts/customer_segments.csv"), fetch("artifacts/explorer_points.csv"), fetch("artifacts/manifest.json"), fetch("artifacts/segmentation.png")]);
    const responses = [summaryResponse, baselineResponse, log1pResponse, validationResponse, assignmentsResponse, explorerResponse, manifestResponse, plotResponse];
    if (!responses.every((response) => response.ok)) throw new Error("One or more artifacts could not be loaded.");
    const buffers = await Promise.all(responses.map((response) => response.arrayBuffer()));
    const [summaryBuffer, baselineBuffer, log1pBuffer, validationBuffer, assignmentsBuffer, explorerBuffer, manifestBuffer] = buffers;
    const summary = parseJson(summaryBuffer); const manifest = parseJson(manifestBuffer);
    const artifactNames = ["summary.json", "baseline_scores.csv", "log1p_scores.csv", "validation_scores.csv", "customer_segments.csv", "explorer_points.csv", "segmentation.png"];
    const artifactBuffers = [summaryBuffer, baselineBuffer, log1pBuffer, validationBuffer, assignmentsBuffer, explorerBuffer, buffers[7]];
    const hashes = Object.fromEntries(await Promise.all(artifactNames.map(async (name, index) => [name, await sha256Hex(artifactBuffers[index])] )));
    const parsed = await validateDashboardArtifacts({ summary, baselineText: new TextDecoder().decode(baselineBuffer), log1pText: new TextDecoder().decode(log1pBuffer), validationText: new TextDecoder().decode(validationBuffer), assignmentsText: new TextDecoder().decode(assignmentsBuffer), explorerText: new TextDecoder().decode(explorerBuffer), manifest, hashes });
    const profiles = buildProfiles(parsed.assignments); state.explorerRows = parsed.explorer;
    renderMetrics(summary); renderFilters(profiles); renderProfiles(profiles); renderScores(parsed.validation, summary.selected_k, summary.selected_preprocessing); renderExplorer();
    $("#feature-select").addEventListener("change", (event) => { state.feature = event.target.value; renderProfiles(profiles); }); $("#x-feature").addEventListener("change", (event) => { state.xFeature = event.target.value; renderExplorer(); }); $("#y-feature").addEventListener("change", (event) => { state.yFeature = event.target.value; renderExplorer(); }); $("#projection-select").addEventListener("change", (event) => { state.projection = event.target.value; document.querySelectorAll(".feature-only-control").forEach((control) => { const select = control.querySelector("select"); select.disabled = state.projection === "pca"; control.classList.toggle("is-disabled", select.disabled); }); renderExplorer(); });
    $("#app-status").textContent = "Artifacts loaded · manifest verified";
  } catch (error) { $("#app-status").textContent = "Artifact verification failed"; $("#profile-grid").innerHTML = `<div class="loading-card"><strong>Could not verify the generated artifacts.</strong><br />Serve this directory with <code>python3 -m http.server 8000</code>, then open <code>http://localhost:8000</code>.</div>`; console.error(error); }
}

setupPhases();
loadDashboard();
