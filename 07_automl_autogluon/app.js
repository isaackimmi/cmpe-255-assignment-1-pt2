const ARTIFACTS = {
  leaderboard: 'artifacts/leaderboard.csv',
  metrics: 'artifacts/metrics.json',
  dataset: 'artifacts/dataset_summary.json',
  final: 'artifacts/final_metrics.json',
};

const state = { leaderboard: [], metrics: {}, dataset: {}, final: {}, selected: 0 };

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
  const [leaderboardResponse, metricsResponse, datasetResponse, finalResponse] = await Promise.all([
    fetch(ARTIFACTS.leaderboard), fetch(ARTIFACTS.metrics), fetch(ARTIFACTS.dataset), fetch(ARTIFACTS.final),
  ]);
  if (![leaderboardResponse, metricsResponse, datasetResponse, finalResponse].every((response) => response.ok)) {
    throw new Error('One or more run artifacts could not be loaded. Regenerate artifacts and start a local HTTP server from this project directory.');
  }
  state.leaderboard = parseCSV(await leaderboardResponse.text());
  state.metrics = await metricsResponse.json();
  state.dataset = await datasetResponse.json();
  state.final = await finalResponse.json();
  if (!state.leaderboard.length) throw new Error('leaderboard.csv does not contain any model rows.');
}

function renderStatus() {
  const status = state.metrics.backend_status || {};
  const isAutoGluon = status.autogluon === 'completed';
  const agStatus = status.autogluon || 'not attempted';
  $('#backend-title').textContent = isAutoGluon ? 'AutoGluon + sklearn comparison complete' : 'Sklearn comparison complete';
  $('#backend-pill').textContent = isAutoGluon ? 'AutoGluon evaluated' : `AutoGluon ${agStatus}`;
  $('#backend-note').textContent = isAutoGluon
    ? 'Both backends were evaluated with the same development-CV/final-holdout roles.'
    : (state.metrics.autogluon_note || `AutoGluon status: ${agStatus}. The sklearn comparison remains available.`);
  $('#status-explainer-copy').textContent = 'The leaderboard is development CV. The selected model’s locked final holdout result is shown separately.';
  $('#last-updated').textContent = `Seed ${state.metrics.random_seed ?? state.dataset.random_seed} · ${state.metrics.ranking_metric || 'cv_roc_auc_mean'} selection`;
}

function renderSnapshot() {
  const leader = state.leaderboard[0];
  const totalFitTime = state.leaderboard.reduce((total, row) => total + (Number(row.cv_fit_seconds_mean) || 0), 0);
  $('#leader-name').textContent = formatName(leader.model);
  $('#leader-foot').textContent = `Rank #${leader.rank} · ${leader.backend}`;
  $('#best-auc').textContent = percent(leader.cv_roc_auc_mean);
  $('#best-accuracy').textContent = percent(state.final.roc_auc);
  $('#model-count').textContent = number(state.leaderboard.length);
  $('#model-count-foot').textContent = `${seconds(totalFitTime)} combined fit time`;
  $('#dataset-caption').textContent = `${formatName(state.dataset.dataset)} · repeated CV + locked holdout`;
  $('#dataset-facts').innerHTML = [
    ['Samples', number(state.dataset.n_samples)], ['Features', number(state.dataset.n_features)],
    ['Development / final', `${number(state.dataset.development_samples)} / ${number(state.dataset.final_test_samples)}`],
    ['Final holdout', percent(state.dataset.test_size)], ['Positive class', state.dataset.positive_class?.name || '—'],
  ].map(([label, value]) => `<span class="dataset-fact"><strong>${label}</strong> ${value}</span>`).join('');
}

function backendLabel(backend) { return backend === 'autogluon' ? 'AutoGluon' : 'sklearn'; }

function renderModelList() {
  const maxFit = Math.max(...state.leaderboard.map((row) => Number(row.cv_fit_seconds_mean) || 0), 1);
  $('#model-list').innerHTML = state.leaderboard.map((row, index) => `
    <article class="model-card ${index === state.selected ? 'selected' : ''}" data-index="${index}" tabindex="0" role="button" aria-label="Inspect ${formatName(row.model)}">
      <span class="model-rank">${String(row.rank).padStart(2, '0')}</span>
      <div class="model-card-header"><h3 class="model-name">${formatName(row.model)}</h3><span class="backend-badge">${backendLabel(row.backend)}</span></div>
      <div class="model-metrics">
        <div class="metric-row"><div class="metric-name"><span>DEV CV ROC-AUC</span><span class="metric-value">${percent(row.cv_roc_auc_mean)}</span></div><div class="metric-bar"><div class="metric-fill fill-auc" style="width:${Math.max(0, Number(row.cv_roc_auc_mean) * 100)}%"></div></div></div>
        <div class="metric-row"><div class="metric-name"><span>CV ACCURACY</span><span class="metric-value">${percent(row.cv_accuracy_mean)}</span></div><div class="metric-bar"><div class="metric-fill fill-accuracy" style="width:${Math.max(0, Number(row.cv_accuracy_mean) * 100)}%"></div></div></div>
        <div class="metric-row"><div class="metric-name"><span>CV FIT TIME</span><span class="metric-value">${seconds(row.cv_fit_seconds_mean)}</span></div><div class="metric-bar"><div class="metric-fill fill-time" style="width:${Math.max(3, (Number(row.cv_fit_seconds_mean) / maxFit) * 100)}%"></div></div></div>
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
    <div class="detail-score"><strong>${percent(row.cv_roc_auc_mean)}</strong><span>DEV CV ROC-AUC<br />SELECTION SIGNAL</span></div>
    <div class="detail-stat-grid"><div class="detail-stat"><span>CV ACCURACY</span><strong>${percent(row.cv_accuracy_mean)}</strong></div><div class="detail-stat"><span>CV F1 SCORE</span><strong>${percent(row.cv_f1_mean)}</strong></div><div class="detail-stat"><span>CV FIT TIME</span><strong>${seconds(row.cv_fit_seconds_mean)}</strong></div></div>
    <p class="detail-note">${row.model === state.final.model ? `Selected by development CV. Final holdout ROC-AUC: ${percent(state.final.roc_auc)}.` : 'Development-CV comparison point; no final holdout score is reported for non-selected models.'}</p>`;
}

function selectModel(index) {
  state.selected = index;
  renderModelList();
  renderDetail();
}

function renderChart() {
  const maxFit = Math.max(...state.leaderboard.map((row) => Number(row.cv_fit_seconds_mean) || 0), 1);
  $('#comparison-chart').innerHTML = state.leaderboard.map((row) => `
    <div class="chart-row"><span class="chart-label">${formatName(row.model)}</span><div class="chart-bars"><div class="chart-bar chart-auc"><span style="width:${Number(row.cv_roc_auc_mean) * 100}%"></span></div><div class="chart-bar chart-accuracy"><span style="width:${Number(row.cv_accuracy_mean) * 100}%"></span></div></div><span class="chart-value">${percent(row.cv_roc_auc_mean)}</span></div>`).join('');
  $('#comparison-chart').setAttribute('title', `CV fit times range from ${seconds(Math.min(...state.leaderboard.map((row) => row.cv_fit_seconds_mean)))} to ${seconds(maxFit)}.`);
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
