const ARTIFACTS = {
  leaderboard: 'artifacts/leaderboard.csv',
  metrics: 'artifacts/metrics.json',
  dataset: 'artifacts/dataset_summary.json',
};

const state = { leaderboard: [], metrics: {}, dataset: {}, selected: 0 };

const $ = (selector) => document.querySelector(selector);
const formatName = (value) => String(value || 'Unknown model')
  .replace(/_/g, ' ')
  .replace(/\b\w/g, (letter) => letter.toUpperCase());
const percent = (value) => value == null || Number.isNaN(Number(value)) ? '—' : `${(Number(value) * 100).toFixed(2)}%`;
const seconds = (value) => value == null || Number.isNaN(Number(value)) ? '—' : `${Number(value).toFixed(4)}s`;
const number = (value) => Number(value).toLocaleString('en-US');

function parseCSV(text) {
  const rows = [];
  let row = [], cell = '', quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '"' && text[index + 1] === '"' && quoted) { cell += '"'; index += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === ',' && !quoted) { row.push(cell); cell = ''; }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[index + 1] === '\n') index += 1;
      row.push(cell); cell = '';
      if (row.some((value) => value.trim() !== '')) rows.push(row);
      row = [];
    } else cell += char;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const headers = rows.shift() || [];
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => {
    const raw = (values[index] || '').trim();
    const value = raw !== '' && !Number.isNaN(Number(raw)) ? Number(raw) : raw;
    return [header.trim(), value];
  })));
}

async function loadArtifacts() {
  const [leaderboardResponse, metricsResponse, datasetResponse] = await Promise.all([
    fetch(ARTIFACTS.leaderboard), fetch(ARTIFACTS.metrics), fetch(ARTIFACTS.dataset),
  ]);
  if (![leaderboardResponse, metricsResponse, datasetResponse].every((response) => response.ok)) {
    throw new Error('One or more artifact files could not be loaded. Start a local HTTP server from this project directory.');
  }
  state.leaderboard = parseCSV(await leaderboardResponse.text());
  state.metrics = await metricsResponse.json();
  state.dataset = await datasetResponse.json();
  if (!state.leaderboard.length) throw new Error('leaderboard.csv does not contain any model rows.');
}

function renderStatus() {
  const isAutoGluon = state.metrics.backend === 'autogluon_plus_sklearn';
  $('#backend-title').textContent = isAutoGluon ? 'AutoGluon + sklearn run complete' : 'Sklearn fallback run complete';
  $('#backend-pill').textContent = isAutoGluon ? 'AutoGluon available' : 'Fallback active';
  $('#backend-note').textContent = isAutoGluon
    ? 'AutoGluon contributed a model to the comparison; sklearn baselines remain visible.'
    : (state.metrics.autogluon_note || 'AutoGluon was not used for this run.');
  $('#status-explainer-copy').textContent = isAutoGluon
    ? 'AutoGluon is an optional search backend; the sklearn baselines provide a stable reference.'
    : 'AutoGluon is optional. The fallback is labeled explicitly and never presented as an AutoGluon run.';
  $('#last-updated').textContent = `Seed ${state.metrics.random_seed ?? state.dataset.random_seed} · ${state.metrics.ranking_metric || 'roc_auc'} ranking`;
}

function renderSnapshot() {
  const leader = state.leaderboard[0];
  const bestAccuracy = [...state.leaderboard].sort((a, b) => b.accuracy - a.accuracy)[0];
  const totalFitTime = state.leaderboard.reduce((total, row) => total + (Number(row.fit_seconds) || 0), 0);
  $('#leader-name').textContent = formatName(leader.model);
  $('#leader-foot').textContent = `Rank #${leader.rank} · ${leader.backend}`;
  $('#best-auc').textContent = percent(leader.roc_auc);
  $('#best-accuracy').textContent = percent(bestAccuracy.accuracy);
  $('#model-count').textContent = number(state.leaderboard.length);
  $('#model-count-foot').textContent = `${seconds(totalFitTime)} combined fit time`;
  $('#dataset-caption').textContent = `${formatName(state.dataset.dataset)} · fixed holdout evaluation`;
  $('#dataset-facts').innerHTML = [
    ['Samples', number(state.dataset.n_samples)], ['Features', number(state.dataset.n_features)],
    ['Train / test', `${number(state.dataset.train_samples)} / ${number(state.dataset.test_samples)}`],
    ['Holdout', percent(state.dataset.test_size)], ['Seed', state.dataset.random_seed],
  ].map(([label, value]) => `<span class="dataset-fact"><strong>${label}</strong> ${value}</span>`).join('');
}

function backendLabel(backend) { return backend === 'autogluon' ? 'AutoGluon' : 'sklearn'; }

function renderModelList() {
  const maxFit = Math.max(...state.leaderboard.map((row) => Number(row.fit_seconds) || 0), 1);
  $('#model-list').innerHTML = state.leaderboard.map((row, index) => `
    <article class="model-card ${index === state.selected ? 'selected' : ''}" data-index="${index}" tabindex="0" role="button" aria-label="Inspect ${formatName(row.model)}">
      <span class="model-rank">${String(row.rank).padStart(2, '0')}</span>
      <div class="model-card-header"><h3 class="model-name">${formatName(row.model)}</h3><span class="backend-badge">${backendLabel(row.backend)}</span></div>
      <div class="model-metrics">
        <div class="metric-row"><div class="metric-name"><span>ROC-AUC</span><span class="metric-value">${percent(row.roc_auc)}</span></div><div class="metric-bar"><div class="metric-fill fill-auc" style="width:${Math.max(0, Number(row.roc_auc) * 100)}%"></div></div></div>
        <div class="metric-row"><div class="metric-name"><span>ACCURACY</span><span class="metric-value">${percent(row.accuracy)}</span></div><div class="metric-bar"><div class="metric-fill fill-accuracy" style="width:${Math.max(0, Number(row.accuracy) * 100)}%"></div></div></div>
        <div class="metric-row"><div class="metric-name"><span>FIT TIME</span><span class="metric-value">${seconds(row.fit_seconds)}</span></div><div class="metric-bar"><div class="metric-fill fill-time" style="width:${Math.max(3, (Number(row.fit_seconds) / maxFit) * 100)}%"></div></div></div>
      </div>
    </article>`).join('');
  document.querySelectorAll('.model-card').forEach((card) => {
    card.addEventListener('click', () => selectModel(Number(card.dataset.index)));
    card.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectModel(Number(card.dataset.index)); } });
  });
}

function renderDetail() {
  const row = state.leaderboard[state.selected];
  if (!row) return;
  $('#detail-title').textContent = formatName(row.model);
  $('#model-select').value = String(state.selected);
  $('#model-detail').innerHTML = `
    <span class="detail-backend">${backendLabel(row.backend).toUpperCase()} · RANK #${row.rank}</span>
    <div class="detail-score"><strong>${percent(row.roc_auc)}</strong><span>TEST ROC-AUC<br />PRIMARY SIGNAL</span></div>
    <div class="detail-stat-grid"><div class="detail-stat"><span>ACCURACY</span><strong>${percent(row.accuracy)}</strong></div><div class="detail-stat"><span>F1 SCORE</span><strong>${percent(row.f1)}</strong></div><div class="detail-stat"><span>FIT TIME</span><strong>${seconds(row.fit_seconds)}</strong></div></div>
    <p class="detail-note">${row.model === state.leaderboard[0].model ? 'Top-ranked on the untouched test split for this run.' : 'A useful comparison point against the current leader.'}</p>`;
}

function selectModel(index) {
  state.selected = index;
  renderModelList();
  renderDetail();
}

function renderChart() {
  const maxFit = Math.max(...state.leaderboard.map((row) => Number(row.fit_seconds) || 0), 1);
  $('#comparison-chart').innerHTML = state.leaderboard.map((row) => `
    <div class="chart-row"><span class="chart-label">${formatName(row.model)}</span><div class="chart-bars"><div class="chart-bar chart-auc"><span style="width:${Number(row.roc_auc) * 100}%"></span></div><div class="chart-bar chart-accuracy"><span style="width:${Number(row.accuracy) * 100}%"></span></div></div><span class="chart-value">${percent(row.roc_auc)}</span></div>`).join('');
  $('#comparison-chart').setAttribute('title', `Fit times range from ${seconds(Math.min(...state.leaderboard.map((row) => row.fit_seconds)))} to ${seconds(maxFit)}.`);
}

function populateSelector() {
  const selector = $('#model-select');
  selector.innerHTML = state.leaderboard.map((row, index) => `<option value="${index}">${formatName(row.model)}</option>`).join('');
  selector.disabled = false;
  selector.addEventListener('change', () => selectModel(Number(selector.value)));
}

function showError(error) {
  const toast = $('#error-toast');
  toast.textContent = error.message;
  toast.hidden = false;
  $('#last-updated').textContent = 'Artifact load failed';
  $('#backend-title').textContent = 'Unable to read run status';
  $('#backend-pill').textContent = 'Needs local server';
}

async function init() {
  try {
    await loadArtifacts();
    renderStatus(); renderSnapshot(); renderModelList(); renderDetail(); renderChart(); populateSelector();
  } catch (error) { showError(error); }
}

init();
