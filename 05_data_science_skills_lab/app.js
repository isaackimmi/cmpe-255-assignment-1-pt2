const modules = {
  clean: { number: '01', kicker: 'INGESTION + VALIDATION', title: 'Clean the signal', description: 'Before analysis, the lab validates the schema, numeric domains, plans, labels, and duplicate policy. Missing values are imputed only where an analysis explicitly needs them.', result: () => `${state.metrics.data_quality.clean_rows} validated rows`, why: 'reliable inputs', icon: '01' },
  explore: { number: '02', kicker: 'EDA + CORRELATION', title: 'Explore relationships', description: 'Observed usage values show descriptive association with renewal and support tickets. The correlations are not causal evidence and exclude the missing usage target.', result: () => `${formatNumber(state.metrics.eda.usage_renewal_correlation)} association`, why: 'find the signal', icon: '02' },
  predict: { number: '03', kicker: 'LINEAR REGRESSION', title: 'Predict usage', description: 'Tenure becomes a simple explanatory feature for monthly usage. A seeded shuffled holdout is scored only on observed test targets; the training-only mean is the baseline.', result: () => `MAE ${formatNumber(state.metrics.regression.mae)}`, why: 'test a baseline', icon: '03' },
  classify: { number: '04', kicker: 'RULE-BASED BASELINE', title: 'Classify renewal', description: 'A fixed, transparent rule marks customers with at least 45 usage and no more than two support tickets as likely to renew, then compares it with a majority-class baseline on a stratified holdout.', result: () => `${formatPercent(state.metrics.classification.accuracy)} held-out`, why: 'make assumptions visible', icon: '04' },
  cluster: { number: '05', kicker: 'SCALED K-MEANS', title: 'Find customer groups', description: 'Z-score scaling prevents monthly usage from overwhelming support tickets. Candidate k values, silhouette separation, inertia, and repeated initializations make the two-group choice inspectable.', result: () => `${state.metrics.clustering.k} customer groups`, why: 'segment the context', icon: '05' },
};

const state = { metrics: null, summary: null };
const $ = (selector) => document.querySelector(selector);
const formatNumber = (value, digits = 2) => Number(value).toFixed(digits);
const formatPercent = (value) => `${Math.round(Number(value) * 100)}%`;

function setText(selector, value) { const element = $(selector); if (element) element.textContent = value; }

function renderMetrics() {
  const { data_quality: quality, eda, regression, classification } = state.metrics;
  document.querySelectorAll('.module-button').forEach((button) => { button.disabled = false; });
  setText('#pulse-value', quality.clean_rows);
  setText('#quality-value', `${quality.clean_rows}/${quality.raw_rows}`);
  setText('#quality-note', `${quality.duplicates_removed} duplicate · ${quality.missing_values_imputed} imputed for analysis`);
  setText('#correlation-value', formatNumber(eda.usage_renewal_correlation));
  setText('#accuracy-value', formatPercent(classification.accuracy));
  setText('#mae-value', formatNumber(regression.mae));
  setText('#raw-rows', quality.raw_rows);
  setText('#duplicates', quality.duplicates_removed);
  setText('#imputed', quality.missing_values_imputed);
  setText('#clean-rows', quality.clean_rows);
  requestAnimationFrame(() => {
    const corr = Math.min(100, Math.abs(Number(eda.usage_renewal_correlation)) * 100);
    const accuracy = Number(classification.accuracy) * 100;
    $('#correlation-progress').style.width = `${corr}%`;
    $('#accuracy-progress').style.width = `${accuracy}%`;
  });
}

function selectModule(key) {
  const module = modules[key];
  document.querySelectorAll('.module-button').forEach((button) => {
    const active = button.dataset.module === key;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-pressed', active ? 'true' : 'false');
  });
  setText('#detail-icon', module.icon);
  setText('#detail-kicker', module.kicker);
  setText('#detail-title', module.title);
  setText('#detail-description', module.description);
  setText('#detail-result', module.result());
  setText('#detail-why', module.why);
}

function selectChart(chart) {
  const isCluster = chart === 'clusters';
  const image = $('#chart-image');
  document.querySelectorAll('.chart-tab').forEach((tab) => {
    const active = tab.dataset.chart === chart;
    tab.classList.toggle('is-active', active);
    tab.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  image.classList.remove('loaded');
  image.alt = isCluster ? 'Customer health clustering scatter plot' : 'Scatter plot of tenure versus monthly usage';
  image.src = isCluster ? 'artifacts/customer_clusters.svg' : 'artifacts/tenure_usage.svg';
  setText('#chart-title', isCluster ? 'Customer health clusters' : 'Tenure × monthly usage');
  setText('#chart-caption', isCluster ? 'Z-score-scaled k-means is shown in original units; colors identify cluster labels.' : 'Observed values show association between tenure and usage; this is not causal evidence.');
}

function markChartLoaded() { $('#chart-image').parentElement.classList.add('loaded'); }

async function loadArtifacts() {
  try {
    const [metricsResponse, summaryResponse] = await Promise.all([fetch('artifacts/metrics.json'), fetch('artifacts/summary.json')]);
    if (!metricsResponse.ok || !summaryResponse.ok) throw new Error('Artifact request failed');
    state.metrics = await metricsResponse.json();
    state.summary = await summaryResponse.json();
    renderMetrics();
    selectModule('clean');
    setText('#artifact-status', 'READY');
    $('#artifact-status').style.color = 'var(--green)';
  } catch (error) {
    setText('#artifact-status', 'RUN LAB FIRST');
    $('#artifact-status').style.color = 'var(--coral)';
    setText('#quality-note', 'Serve this folder, then reload.');
    setText('#chart-loading', 'Run python3 run_lab.py, then serve this folder');
    document.querySelectorAll('.module-button').forEach((button) => { button.disabled = true; });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.module-button').forEach((button) => button.addEventListener('click', () => selectModule(button.dataset.module)));
  document.querySelectorAll('.chart-tab').forEach((button) => button.addEventListener('click', () => selectChart(button.dataset.chart)));
  $('#chart-image').addEventListener('load', markChartLoaded);
  $('#chart-image').addEventListener('error', () => setText('#chart-loading', 'SVG artifact unavailable'));
  if ($('#chart-image').complete) markChartLoaded();
  loadArtifacts();
});
