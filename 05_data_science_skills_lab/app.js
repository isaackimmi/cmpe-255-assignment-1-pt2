const modules = {
  clean: { number: '01', kicker: 'INGESTION + VALIDATION', title: 'Clean the signal', description: 'Before analysis, the lab validates the schema, numeric domains, plans, labels, and duplicate policy. Missing values are imputed only where an analysis explicitly needs them.', result: () => `${state.metrics.data_quality.clean_rows} validated rows`, why: 'reliable inputs', icon: '01' },
  explore: { number: '02', kicker: 'EDA + CORRELATION', title: 'Explore relationships', description: 'Observed usage values show descriptive association with renewal and support tickets. The correlations are not causal evidence and exclude the missing usage target.', result: () => `${formatNumber(state.metrics.eda.usage_renewal_correlation)} association`, why: 'find the signal', icon: '02' },
  predict: { number: '03', kicker: 'LINEAR REGRESSION', title: 'Predict usage', description: 'Tenure becomes a simple explanatory feature for monthly usage. A seeded shuffled holdout is scored only on observed test targets; the training-only mean is the baseline.', result: () => `MAE ${formatNumber(state.metrics.regression.mae)}`, why: 'test a baseline', icon: '03' },
  classify: { number: '04', kicker: 'RULE-BASED BASELINE', title: 'Classify renewal', description: 'A fixed, transparent rule marks customers with at least 45 usage and no more than two support tickets as likely to renew, then compares it with a majority-class baseline on a stratified holdout.', result: () => `${formatPercent(state.metrics.classification.accuracy)} held-out`, why: 'make assumptions visible', icon: '04' },
  cluster: { number: '05', kicker: 'SCALED K-MEANS', title: 'Find customer groups', description: 'Z-score scaling prevents monthly usage from overwhelming support tickets. Candidate k values, silhouette separation, inertia, and repeated initializations make the two-group choice inspectable.', result: () => `${state.metrics.clustering.k} customer groups`, why: 'segment the context', icon: '05' },
};

const state = { metrics: null, summary: null };
const chartState = { kind: 'tenure', filters: { plan: 'all', renewal: 'all', cluster: 'all' } };
const $ = (selector) => document.querySelector(selector);
const formatNumber = (value, digits = 2) => Number(value).toFixed(digits);
const formatPercent = (value, digits = 0) => `${(Number(value) * 100).toFixed(digits)}%`;
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
const setText = (selector, value) => { const element = $(selector); if (element) element.textContent = value; };
const setHTML = (selector, value) => { const element = $(selector); if (element) element.innerHTML = value; };

function clusterName(index) {
  const center = state.metrics.clustering.centers[index];
  const centers = state.metrics.clustering.centers;
  const usageAverage = centers.reduce((total, item) => total + item[0], 0) / centers.length;
  const ticketsAverage = centers.reduce((total, item) => total + item[1], 0) / centers.length;
  const usage = center[0] <= usageAverage ? 'lower-use' : 'higher-use';
  const tickets = center[1] >= ticketsAverage ? 'higher-support' : 'lower-support';
  return `${usage} / ${tickets}`;
}

function renderMetrics() {
  const { data_quality: quality, eda, regression, classification } = state.metrics;
  document.querySelectorAll('.module-button').forEach((button) => { button.disabled = false; });
  setText('#pulse-value', quality.clean_rows);
  setText('#quality-value', `${quality.clean_rows}/${quality.raw_rows}`);
  setText('#quality-note', `${quality.duplicates_removed} duplicate · ${quality.missing_values_imputed} imputed for analysis`);
  setText('#correlation-value', formatNumber(eda.usage_renewal_correlation));
  setText('#correlation-note', `descriptive r · n=${eda.observed_usage_rows} observed`);
  setText('#accuracy-value', formatPercent(classification.accuracy));
  setText('#accuracy-note', `holdout n=${classification.test_rows} · baseline ${formatPercent(classification.majority_baseline_accuracy)}`);
  setText('#mae-value', formatNumber(regression.mae));
  setText('#mae-note', `observed test n=${regression.scored_rows} · baseline ${formatNumber(regression.mean_baseline_mae)}`);
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

function evidenceTable(headers, rows, className = '') {
  return `<div class="evidence-table-wrap"><table class="evidence-table ${className}"><thead><tr>${headers.map((header) => `<th>${escapeHTML(header)}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

function renderEvidence(key) {
  if (!state.metrics || !state.summary) return;
  const { data_quality: quality, eda, regression, classification, clustering } = state.metrics;
  let content = '';
  if (key === 'clean') {
    const missing = Object.entries(quality.missing_values_by_column).map(([column, count]) => `${escapeHTML(column)}: ${count}`).join(' · ');
    content = `<div class="evidence-summary"><strong>${quality.clean_rows} clean rows</strong><span>${quality.raw_rows} raw − ${quality.duplicates_removed} identical duplicate</span></div>${evidenceTable(['Validation signal', 'Observed'], [['Missing values', `${quality.missing_values_imputed} value${quality.missing_values_imputed === 1 ? '' : 's'} imputed for analysis`], ['Missing by column', missing], ['Policy', 'invalid domains and conflicting IDs rejected']])}`;
  } else if (key === 'explore') {
    content = `<div class="evidence-summary"><strong>n=${eda.observed_usage_rows} observed usage rows</strong><span>one missing usage value excluded</span></div>${evidenceTable(['Relationship', 'Pearson r', 'Read as'], [['Usage ↔ renewal', formatNumber(eda.usage_renewal_correlation, 3), 'descriptive association'], ['Usage ↔ tickets', formatNumber(eda.usage_ticket_correlation, 3), 'descriptive association']])}<p class="evidence-note">Association is not causal evidence; this is a compact synthetic fixture.</p>`;
  } else if (key === 'predict') {
    const delta = regression.mean_baseline_mae - regression.mae;
    const predictions = state.summary.regression_predictions.map((row) => [escapeHTML(row.customer_id), formatNumber(row.actual_usage, 1), formatNumber(row.predicted_usage, 1), formatNumber(row.actual_usage - row.predicted_usage, 1)]);
    content = `<div class="evidence-summary"><strong>n=${regression.scored_rows} observed test targets</strong><span>one-feature regression baseline · tenure → usage</span></div>${evidenceTable(['Metric', 'Model', 'Mean baseline'], [['MAE', formatNumber(regression.mae), formatNumber(regression.mean_baseline_mae)], ['RMSE', formatNumber(regression.rmse), formatNumber(regression.mean_baseline_rmse)], ['R²', formatNumber(regression.r2), '—']])}<p class="evidence-note">Model MAE is ${formatNumber(Math.abs(delta))} lower than the training-mean baseline on this split. Results are high-variance, not a production forecast.</p>${evidenceTable(['Customer', 'Actual', 'Predicted', 'Residual'], predictions, 'compact-table')}`;
  } else if (key === 'classify') {
    const matrix = classification.confusion_matrix;
    const delta = classification.accuracy - classification.majority_baseline_accuracy;
    content = `<div class="evidence-summary"><strong>${formatPercent(classification.accuracy, 1)} on n=${classification.test_rows} holdout cases</strong><span>fixed rule · ${Object.values(classification.test_feature_imputed).reduce((sum, value) => sum + value, 0)} test feature imputed</span></div>${evidenceTable(['Metric', 'Rule', 'Majority baseline'], [['Accuracy', formatPercent(classification.accuracy, 1), formatPercent(classification.majority_baseline_accuracy, 1)], ['F1', formatNumber(classification.f1, 3), '—'], ['Specificity', formatPercent(classification.specificity, 1), '—'], ['Balanced accuracy', formatPercent(classification.balanced_accuracy, 1), '—']])}<p class="evidence-note">Confusion matrix [actual 0/1 × predicted 0/1]: <strong>[[${matrix[0][0]}, ${matrix[0][1]}], [${matrix[1][0]}, ${matrix[1][1]}]]</strong>. The rule is ${delta === 0 ? 'the same as' : `${formatNumber(Math.abs(delta) * 100, 1)} points ${delta > 0 ? 'above' : 'below'}`} the majority baseline here.</p>`;
  } else {
    const candidateRows = clustering.candidate_k.map((candidate) => [candidate.k === clustering.k ? `<strong>${candidate.k} selected</strong>` : candidate.k, formatNumber(candidate.inertia), formatNumber(candidate.silhouette, 3), candidate.n_init]);
    const profileRows = clustering.centers.map((center, index) => [escapeHTML(clusterName(index)), clustering.cluster_sizes[index], formatNumber(center[0], 1), formatNumber(center[1], 1)]);
    content = `<div class="evidence-summary"><strong>${clustering.k} descriptive groups</strong><span>z-score scaled · ${clustering.n_init} initializations · silhouette ${formatNumber(clustering.silhouette, 3)}</span></div>${evidenceTable(['Candidate k', 'Inertia', 'Silhouette', 'Starts'], candidateRows)}${evidenceTable(['Interpretive label', 'n', 'Usage center', 'Tickets center'], profileRows)}<p class="evidence-note">Cluster labels are descriptive, not causal; IDs have no intrinsic meaning.</p>`;
  }
  setHTML('#detail-evidence', content);
}

function selectModule(key) {
  if (!state.metrics) return;
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
  renderEvidence(key);
}

function svgElement(tag, attributes = {}, text = '') {
  const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value));
  if (text) element.textContent = text;
  return element;
}

function chartRows() {
  const source = chartState.kind === 'clusters' ? state.summary.analysis_rows : state.summary.rows;
  return source.filter((row) => {
    if (chartState.kind === 'tenure' && (row.tenure_months === null || row.monthly_usage === null)) return false;
    if (chartState.filters.plan !== 'all' && row.plan !== chartState.filters.plan) return false;
    if (chartState.filters.renewal !== 'all' && String(row.renewed) !== chartState.filters.renewal) return false;
    if (chartState.kind === 'clusters' && chartState.filters.cluster !== 'all' && String(row.cluster) !== chartState.filters.cluster) return false;
    return true;
  });
}

function showChartTooltip(row) {
  const cluster = chartState.kind === 'clusters' ? ` · ${clusterName(row.cluster)}` : '';
  setText('#chart-tooltip', `${row.customer_id} · ${row.plan} · tenure ${formatNumber(row.tenure_months, 0)} mo · usage ${formatNumber(row.monthly_usage, 1)} · tickets ${formatNumber(row.support_tickets, 0)} · ${row.renewed ? 'renewed' : 'not renewed'}${cluster}`);
  $('#chart-tooltip').classList.add('is-visible');
}

function hideChartTooltip() { $('#chart-tooltip').classList.remove('is-visible'); }

function renderChartTable(rows) {
  const headers = chartState.kind === 'clusters' ? ['Customer', 'Plan', 'Usage', 'Tickets', 'Group'] : ['Customer', 'Plan', 'Tenure', 'Usage', 'Renewal'];
  setHTML('#chart-table-head', `<tr>${headers.map((header) => `<th scope="col">${header}</th>`).join('')}</tr>`);
  setHTML('#chart-table-body', rows.map((row) => {
    const cells = chartState.kind === 'clusters'
      ? [row.customer_id, row.plan, formatNumber(row.monthly_usage, 1), formatNumber(row.support_tickets, 0), clusterName(row.cluster)]
      : [row.customer_id, row.plan, `${formatNumber(row.tenure_months, 0)} mo`, formatNumber(row.monthly_usage, 1), row.renewed ? 'Renewed' : 'Not renewed'];
    return `<tr>${cells.map((cell) => `<td>${escapeHTML(cell)}</td>`).join('')}</tr>`;
  }).join(''));
}

function renderChart() {
  if (!state.summary || !state.metrics) return;
  const svg = $('#chart-svg');
  const rows = chartRows();
  const allRows = chartState.kind === 'clusters' ? state.summary.analysis_rows : state.summary.rows.filter((row) => row.tenure_months !== null && row.monthly_usage !== null);
  const xKey = chartState.kind === 'clusters' ? 'monthly_usage' : 'tenure_months';
  const yKey = chartState.kind === 'clusters' ? 'support_tickets' : 'monthly_usage';
  const xLabel = chartState.kind === 'clusters' ? 'monthly usage' : 'tenure (months)';
  const yLabel = chartState.kind === 'clusters' ? 'support tickets' : 'monthly usage';
  const width = 700; const height = 420; const margin = { top: 62, right: 28, bottom: 61, left: 66 };
  const values = (key, source) => source.map((row) => Number(row[key]));
  const domain = (numbers) => {
    if (!numbers.length) return [0, 1];
    const low = Math.min(...numbers); const high = Math.max(...numbers);
    if (low === high) { const pad = Math.max(Math.abs(low) * 0.05, 1); return [low - pad, high + pad]; }
    const pad = (high - low) * 0.08; return [low - pad, high + pad];
  };
  const xDomain = domain(values(xKey, allRows)); const yDomain = domain(values(yKey, allRows));
  const x = (value) => margin.left + (value - xDomain[0]) / (xDomain[1] - xDomain[0]) * (width - margin.left - margin.right);
  const y = (value) => height - margin.bottom - (value - yDomain[0]) / (yDomain[1] - yDomain[0]) * (height - margin.top - margin.bottom);
  svg.replaceChildren();
  svg.appendChild(svgElement('title', { id: 'chart-svg-title' }, chartState.kind === 'clusters' ? 'Customer health clustering scatter plot' : 'Tenure versus monthly usage scatter plot'));
  svg.appendChild(svgElement('desc', { id: 'chart-svg-description' }, `${rows.length} filtered rows. Use the table below or focus a point to inspect a customer.`));
  svg.appendChild(svgElement('rect', { x: 0, y: 0, width, height, fill: '#ffffff' }));
  svg.appendChild(svgElement('text', { x: width / 2, y: 25, 'text-anchor': 'middle', class: 'svg-title' }, chartState.kind === 'clusters' ? 'Customer health clusters' : 'Tenure vs monthly usage'));
  const legendItems = chartState.kind === 'clusters'
    ? state.metrics.clustering.centers.map((_, index) => ({ color: ['#2858d8', '#e9b94f', '#438c71', '#f07861', '#7b61a8', '#2e9aa5'][index], label: clusterName(index) }))
    : [{ color: '#2858d8', label: 'renewed' }, { color: '#f07861', label: 'not renewed' }];
  let legendX = margin.left;
  legendItems.forEach((item) => {
    svg.appendChild(svgElement('circle', { cx: legendX, cy: 45, r: 5, fill: item.color }));
    svg.appendChild(svgElement('text', { x: legendX + 10, y: 49, class: 'svg-legend' }, item.label));
    legendX += Math.max(90, item.label.length * 6 + 30);
  });
  for (const fraction of [0, 0.5, 1]) {
    const xValue = xDomain[0] + fraction * (xDomain[1] - xDomain[0]);
    const yValue = yDomain[0] + fraction * (yDomain[1] - yDomain[0]);
    const xPosition = margin.left + fraction * (width - margin.left - margin.right);
    const yPosition = height - margin.bottom - fraction * (height - margin.top - margin.bottom);
    svg.appendChild(svgElement('line', { x1: xPosition, y1: margin.top, x2: xPosition, y2: height - margin.bottom, class: 'svg-gridline' }));
    svg.appendChild(svgElement('line', { x1: margin.left, y1: yPosition, x2: width - margin.right, y2: yPosition, class: 'svg-gridline' }));
    svg.appendChild(svgElement('text', { x: xPosition, y: height - margin.bottom + 19, 'text-anchor': 'middle', class: 'svg-tick' }, formatNumber(xValue, 1)));
    svg.appendChild(svgElement('text', { x: margin.left - 10, y: yPosition + 4, 'text-anchor': 'end', class: 'svg-tick' }, formatNumber(yValue, 1)));
  }
  svg.appendChild(svgElement('line', { x1: margin.left, y1: height - margin.bottom, x2: width - margin.right, y2: height - margin.bottom, class: 'svg-axis' }));
  svg.appendChild(svgElement('line', { x1: margin.left, y1: margin.top, x2: margin.left, y2: height - margin.bottom, class: 'svg-axis' }));
  svg.appendChild(svgElement('text', { x: width / 2, y: height - 10, 'text-anchor': 'middle', class: 'svg-label' }, xLabel));
  svg.appendChild(svgElement('text', { transform: `translate(16 ${height / 2}) rotate(-90)`, 'text-anchor': 'middle', class: 'svg-label' }, yLabel));
  if (!rows.length) svg.appendChild(svgElement('text', { x: width / 2, y: height / 2, 'text-anchor': 'middle', class: 'svg-empty' }, 'No rows match these filters'));
  rows.forEach((row) => {
    const color = chartState.kind === 'clusters' ? ['#2858d8', '#e9b94f', '#438c71', '#f07861', '#7b61a8', '#2e9aa5'][row.cluster] : (row.renewed ? '#2858d8' : '#f07861');
    const circle = svgElement('circle', { cx: x(row[xKey]), cy: y(row[yKey]), r: 6, fill: color, class: 'data-point', tabindex: 0, role: 'img', 'aria-label': `${row.customer_id}, ${row.plan}, ${chartState.kind === 'clusters' ? clusterName(row.cluster) : row.renewed ? 'renewed' : 'not renewed'}` });
    circle.appendChild(svgElement('title', {}, `${row.customer_id}: ${formatNumber(row[xKey], 1)} × ${formatNumber(row[yKey], 1)}`));
    circle.addEventListener('mouseenter', () => showChartTooltip(row));
    circle.addEventListener('focus', () => showChartTooltip(row));
    circle.addEventListener('mouseleave', hideChartTooltip);
    circle.addEventListener('blur', hideChartTooltip);
    svg.appendChild(circle);
  });
  if (chartState.kind === 'clusters') {
    state.metrics.clustering.centers.forEach((center, index) => {
      svg.appendChild(svgElement('path', { d: `M ${x(center[0]) - 8} ${y(center[1]) - 8} L ${x(center[0]) + 8} ${y(center[1]) + 8} M ${x(center[0]) + 8} ${y(center[1]) - 8} L ${x(center[0]) - 8} ${y(center[1]) + 8}`, class: 'cluster-center' }));
      svg.appendChild(svgElement('text', { x: x(center[0]) + 11, y: y(center[1]) - 10, class: 'cluster-label' }, clusterName(index)));
    });
  }
  setText('#chart-count', `${rows.length} of ${allRows.length} points shown`);
  setText('#chart-data-note', chartState.kind === 'clusters' ? '23 clean rows · 1 usage value median-imputed for clustering' : `22 observed usage rows · ${state.metrics.data_quality.missing_values_by_column.monthly_usage} missing usage row omitted`);
  renderChartTable(rows);
  $('#chart-loading').style.display = 'none';
}

function populateClusterFilter() {
  const select = $('#cluster-filter');
  select.innerHTML = '<option value="all">All groups</option>';
  state.metrics.clustering.centers.forEach((_, index) => {
    const option = document.createElement('option'); option.value = String(index); option.textContent = clusterName(index); select.appendChild(option);
  });
}

function selectChart(chart) {
  chartState.kind = chart;
  const isCluster = chart === 'clusters';
  document.querySelectorAll('.chart-tab').forEach((tab) => {
    const active = tab.dataset.chart === chart;
    tab.classList.toggle('is-active', active);
    tab.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  const panel = $('#chart-panel');
  panel.setAttribute('aria-labelledby', isCluster ? 'chart-tab-clusters' : 'chart-tab-tenure');
  $('#cluster-filter-wrap').hidden = !isCluster;
  setText('#chart-title', isCluster ? 'Customer health clusters' : 'Tenure × monthly usage');
  setText('#chart-caption', isCluster ? 'Scaled k-means is shown in original units; descriptive labels summarize the numeric centers.' : 'Observed values show association between tenure and usage; this is not causal evidence.');
  hideChartTooltip();
  renderChart();
}

async function loadArtifacts() {
  try {
    const [metricsResponse, summaryResponse] = await Promise.all([fetch('artifacts/metrics.json'), fetch('artifacts/summary.json')]);
    if (!metricsResponse.ok || !summaryResponse.ok) throw new Error('Artifact request failed');
    state.metrics = await metricsResponse.json();
    state.summary = await summaryResponse.json();
    renderMetrics();
    populateClusterFilter();
    selectModule('clean');
    selectChart('tenure');
    setText('#artifact-status', 'READY');
    $('#artifact-status').style.color = 'var(--green)';
  } catch (error) {
    setText('#artifact-status', 'RUN LAB FIRST');
    $('#artifact-status').style.color = 'var(--coral)';
    setText('#quality-note', 'Serve this folder, then reload.');
    setText('#chart-loading', 'Run python3 run_lab.py, then serve this folder');
    document.querySelectorAll('.module-button, .chart-tab, select').forEach((button) => { button.disabled = true; });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.module-button').forEach((button) => button.addEventListener('click', () => selectModule(button.dataset.module)));
  document.querySelectorAll('.chart-tab').forEach((button) => button.addEventListener('click', () => selectChart(button.dataset.chart)));
  $('#plan-filter').addEventListener('change', (event) => { chartState.filters.plan = event.target.value; renderChart(); });
  $('#renewal-filter').addEventListener('change', (event) => { chartState.filters.renewal = event.target.value; renderChart(); });
  $('#cluster-filter').addEventListener('change', (event) => { chartState.filters.cluster = event.target.value; renderChart(); });
  $('#reset-filters').addEventListener('click', () => { chartState.filters = { plan: 'all', renewal: 'all', cluster: 'all' }; $('#plan-filter').value = 'all'; $('#renewal-filter').value = 'all'; $('#cluster-filter').value = 'all'; renderChart(); });
  loadArtifacts();
});
