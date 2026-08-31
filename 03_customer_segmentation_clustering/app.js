const state = { filter: "all", feature: "spend_score" };
const featureLabels = {
  annual_income_k: "Annual income",
  spend_score: "Spend score",
  purchase_frequency: "Purchase frequency",
  avg_order_value: "Average order value"
};
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

function parseCsv(text) {
  const [header, ...lines] = text.trim().split(/\r?\n/);
  const keys = header.split(",");
  return lines.filter(Boolean).map((line) => {
    const values = line.split(",");
    return Object.fromEntries(keys.map((key, index) => [key, Number.isNaN(Number(values[index])) ? values[index] : Number(values[index])]));
  });
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

function renderFilters(profiles) {
  $("#segment-filters").innerHTML = profiles.map((profile) => `<button class="filter-button" data-filter="${profile.cluster}">Segment ${profile.cluster}</button>`).join("");
  document.querySelectorAll(".filter-button").forEach((button) => button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll(".filter-button").forEach((item) => item.classList.toggle("is-active", item.dataset.filter === state.filter));
    renderProfiles(profiles);
  }));
}

function renderProfiles(profiles) {
  const visible = state.filter === "all" ? profiles : profiles.filter((profile) => String(profile.cluster) === state.filter);
  const maxValue = Math.max(...profiles.map((profile) => profile.means[state.feature]));
  $("#profile-grid").innerHTML = visible.map((profile, index) => {
    const accent = index % 3 === 1 ? "accent-orange" : index % 3 === 2 ? "accent-yellow" : "";
    const share = Math.round((profile.count / profiles.reduce((sum, item) => sum + item.count, 0)) * 100);
    const bar = Math.max(7, Math.round((profile.means[state.feature] / maxValue) * 100));
    return `<article class="profile-card ${accent}">
      <div class="profile-top"><div><span class="segment-index">SEGMENT ${profile.cluster}</span><h3>${profile.name}</h3><p class="profile-subtitle">${profile.subtitle}</p></div><div class="count-box"><strong>${profile.count}</strong><small>${share}% of sample</small></div></div>
      <div class="profile-stat"><div class="stat-label"><span>${featureLabels[state.feature]}</span><span>${formatFeature(state.feature, profile.means[state.feature])}</span></div><div class="bar-track"><div class="bar-fill" style="width:${bar}%"></div></div></div>
      <div class="stat-list"><div><span>Income</span><strong>${formatFeature("annual_income_k", profile.means.annual_income_k)}</strong></div><div><span>Spend score</span><strong>${formatNumber(profile.means.spend_score, 1)}</strong></div><div><span>Frequency</span><strong>${formatFeature("purchase_frequency", profile.means.purchase_frequency)}</strong></div><div><span>Avg order</span><strong>${formatFeature("avg_order_value", profile.means.avg_order_value)}</strong></div></div>
      <div class="profile-foot">${profile.guidance}</div>
    </article>`;
  }).join("");
}

function renderScores(scores, selectedK, selectedPreprocessing) {
  $("#score-body").innerHTML = scores.map((row) => `<tr class="${Number(row.k) === Number(selectedK) && row.preprocessing === selectedPreprocessing ? "selected" : ""}"><td>${row.preprocessing === "log1p" ? "log1p" : "standard"}</td><td>${row.k}</td><td>${formatNumber(row.silhouette_mean, 4)} ± ${formatNumber(row.silhouette_std, 4)}</td><td>${formatNumber(row.stability_ari_mean, 4)}</td></tr>`).join("");
}

async function sha256Hex(buffer) {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function parseJson(buffer) {
  return JSON.parse(new TextDecoder().decode(buffer));
}

async function validateDashboardArtifacts({ summary, baselineText, log1pText, validationText, assignmentsText, manifest, hashes }) {
  const baseline = parseCsv(baselineText);
  const log1p = parseCsv(log1pText);
  const validation = parseCsv(validationText);
  const assignments = parseCsv(assignmentsText);
  const expectedFeatures = summary.features || [];
  const assignmentKeys = assignments.length ? Object.keys(assignments[0]) : [];
  const clusters = [...new Set(assignments.map((row) => Number(row.cluster)))].sort((a, b) => a - b);
  const expectedClusters = Array.from({ length: Number(summary.selected_k) }, (_, index) => index);
  if (manifest.n_customers !== summary.n_customers || manifest.selected_k !== summary.selected_k ||
      JSON.stringify(manifest.features) !== JSON.stringify(expectedFeatures) ||
      assignments.length !== Number(summary.n_customers) ||
      JSON.stringify(assignmentKeys) !== JSON.stringify([...expectedFeatures, "cluster"]) ||
      JSON.stringify(clusters) !== JSON.stringify(expectedClusters) ||
      baseline.length !== 6 || log1p.length !== 6 || validation.length !== 12) {
    throw new Error("Artifact metadata, schema, or row-count consistency check failed.");
  }
  const selectedRows = validation.filter((row) => row.preprocessing === summary.selected_preprocessing && Number(row.k) === Number(summary.selected_k));
  if (selectedRows.length !== 1 || !Number.isFinite(selectedRows[0].silhouette_mean) || !Number.isFinite(selectedRows[0].stability_ari_mean) ||
      Math.abs(selectedRows[0].silhouette_mean - Number(summary.validation.silhouette_mean)) > 1e-9 ||
      Math.abs(selectedRows[0].stability_ari_mean - Number(summary.validation.stability_ari_mean)) > 1e-9) {
    throw new Error("Selected validation result is missing or invalid.");
  }
  for (const [name, expected] of Object.entries(manifest.hashes || {})) {
    if (!hashes[name] || hashes[name] !== expected) throw new Error(`Manifest hash mismatch: ${name}`);
  }
}

function setupPhases() {
  document.querySelectorAll(".phase-button").forEach((button) => button.addEventListener("click", () => {
    const content = phaseContent[button.dataset.phase];
    document.querySelectorAll(".phase-button").forEach((item) => { item.classList.toggle("is-active", item === button); item.setAttribute("aria-selected", item === button ? "true" : "false"); });
    $("#phase-number").textContent = content[0];
    $("#phase-title").textContent = content[1];
    $("#phase-description").textContent = content[2];
    $("#phase-callout").textContent = content[3];
  }));
}

async function loadDashboard() {
  try {
    const [summaryResponse, baselineResponse, log1pResponse, validationResponse, assignmentsResponse, manifestResponse, plotResponse] = await Promise.all([
      fetch("artifacts/summary.json"),
      fetch("artifacts/baseline_scores.csv"),
      fetch("artifacts/log1p_scores.csv"),
      fetch("artifacts/validation_scores.csv"),
      fetch("artifacts/customer_segments.csv"),
      fetch("artifacts/manifest.json"),
      fetch("artifacts/segmentation.png")
    ]);
    const responses = [summaryResponse, baselineResponse, log1pResponse, validationResponse, assignmentsResponse, manifestResponse, plotResponse];
    if (!responses.every((response) => response.ok)) throw new Error("One or more artifacts could not be loaded.");
    const buffers = await Promise.all(responses.map((response) => response.arrayBuffer()));
    const [summaryBuffer, baselineBuffer, log1pBuffer, validationBuffer, assignmentsBuffer, manifestBuffer, plotBuffer] = buffers;
    const summary = parseJson(summaryBuffer);
    const manifest = parseJson(manifestBuffer);
    const artifactNames = ["summary.json", "baseline_scores.csv", "log1p_scores.csv", "validation_scores.csv", "customer_segments.csv", "segmentation.png"];
    const hashes = Object.fromEntries(await Promise.all(artifactNames.map(async (name, index) => [name, await sha256Hex(buffers[index === 5 ? 6 : index])])));
    const baselineText = new TextDecoder().decode(baselineBuffer);
    const log1pText = new TextDecoder().decode(log1pBuffer);
    const validationText = new TextDecoder().decode(validationBuffer);
    const assignmentsText = new TextDecoder().decode(assignmentsBuffer);
    await validateDashboardArtifacts({ summary, baselineText, log1pText, validationText, assignmentsText, manifest, hashes });
    const profiles = buildProfiles(parseCsv(assignmentsText));
    renderMetrics(summary);
    renderFilters(profiles);
    renderProfiles(profiles);
    renderScores(parseCsv(validationText), summary.selected_k, summary.selected_preprocessing);
    $("#feature-select").addEventListener("change", (event) => { state.feature = event.target.value; renderProfiles(profiles); });
    $("#app-status").textContent = "Artifacts loaded · manifest verified";
  } catch (error) {
    $("#app-status").textContent = "Artifact load failed";
    $("#profile-grid").innerHTML = `<div class="loading-card"><strong>Could not load the generated artifacts.</strong><br />Serve this directory with <code>python3 -m http.server 8000</code>, then open <code>http://localhost:8000</code>.</div>`;
    console.error(error);
  }
}

setupPhases();
loadDashboard();
