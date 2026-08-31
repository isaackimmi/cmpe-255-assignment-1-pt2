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
  prep: ["03 / DATA PREPARATION", "Shape the signals before measuring distance.", "Impossible synthetic values are clipped; income and average order value receive log1p before all four features are standardized.", "Preprocessing changes what ‘similar’ means, so it belongs in the story."],
  model: ["04 / MODELING", "Let K-Means test a small range of shapes.", "K-Means is fit for k=2 through 7 with 25 initializations and seed 255. The selected assignments are exported with the raw feature values.", "The cluster IDs are labels, not rankings — their names here are interpretive aids."],
  evaluate: ["05 / EVALUATION", "Prefer signal that is compact and separated.", "Silhouette is the primary selection metric; Calinski–Harabasz and Davies–Bouldin add context. PCA is used only to make the four-dimensional result visible.", "Internal metrics do not establish campaign lift, stability, fairness, or causality."],
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
  if (means.cluster === frequencyLeader.means.cluster) return ["Power shoppers", "High intent · high value", "Protect loyalty and reward cadence"];
  if (means.cluster === aovLeader.means.cluster) return ["Premium occasionals", "High basket · selective cadence", "Build high-touch moments"];
  return ["Value starters", "Entry value · growth headroom", "Create a path to repeat"];
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
  $("#selected-model").textContent = `K-Means · k=${summary.selected_k}`;
  $("#run-size").textContent = `${summary.n_customers} customers · seed ${summary.seed}`;
  $("#silhouette").textContent = formatNumber(summary.silhouette, 4);
  $("#calinski").textContent = formatNumber(summary.calinski_harabasz, 2);
  $("#davies").textContent = formatNumber(summary.davies_bouldin, 4);
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

function renderScores(scores, selectedK) {
  $("#score-body").innerHTML = scores.map((row) => `<tr class="${Number(row.k) === Number(selectedK) ? "selected" : ""}"><td>${row.k}</td><td>${formatNumber(row.silhouette, 4)}</td><td>${formatNumber(row.calinski_harabasz, 1)}</td><td>${formatNumber(row.davies_bouldin, 3)}</td></tr>`).join("");
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
    const [summaryResponse, scoresResponse, assignmentsResponse] = await Promise.all([
      fetch("artifacts/summary.json"),
      fetch("artifacts/improved_scores.csv"),
      fetch("artifacts/customer_segments.csv")
    ]);
    if (![summaryResponse, scoresResponse, assignmentsResponse].every((response) => response.ok)) throw new Error("One or more artifacts could not be loaded.");
    const [summary, scoresText, assignmentsText] = await Promise.all([summaryResponse.json(), scoresResponse.text(), assignmentsResponse.text()]);
    const profiles = buildProfiles(parseCsv(assignmentsText));
    renderMetrics(summary);
    renderFilters(profiles);
    renderProfiles(profiles);
    renderScores(parseCsv(scoresText), summary.selected_k);
    $("#feature-select").addEventListener("change", (event) => { state.feature = event.target.value; renderProfiles(profiles); });
    $("#app-status").textContent = "Artifacts loaded · run verified";
  } catch (error) {
    $("#app-status").textContent = "Artifact load failed";
    $("#profile-grid").innerHTML = `<div class="loading-card"><strong>Could not load the generated artifacts.</strong><br />Serve this directory with <code>python3 -m http.server 8000</code>, then open <code>http://localhost:8000</code>.</div>`;
    console.error(error);
  }
}

setupPhases();
loadDashboard();
