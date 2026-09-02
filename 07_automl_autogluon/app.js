const ARTIFACTS = {
  leaderboard: 'artifacts/leaderboard.csv',
  metrics: 'artifacts/metrics.json',
  dataset: 'artifacts/dataset_summary.json',
  final: 'artifacts/final_metrics.json',
  cvScores: 'artifacts/cv_scores.json',
};

const state = {
  leaderboard: [], metrics: {}, dataset: {}, final: {}, cvScores: {},
  selectedModel: null, sortKey: 'roc_auc', backendFilter: 'all', tieOnly: false,
};

const $ = (selector) => document.querySelector(selector);
const formatName = (value) => String(value || 'Unknown model').replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const percent = (value) => value == null || Number.isNaN(Number(value)) ? '—' : `${(Number(value) * 100).toFixed(2)}%`;
const seconds = (value) => value == null || Number.isNaN(Number(value)) ? '—' : `${Number(value).toFixed(4)}s`;
const number = (value) => Number(value).toLocaleString('en-US');

function parseCSV(text) {
  const rows = []; let row = [], cell = '', quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '"' && text[index + 1] === '"' && quoted) { cell += '"'; index += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === ',' && !quoted) { row.push(cell); cell = ''; }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[index + 1] === '\n') index += 1;
      row.push(cell); cell = ''; if (row.some((value) => value.trim() !== '')) rows.push(row); row = [];
    } else cell += char;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const headers = rows.shift() || [];
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => {
    const raw = (values[index] || '').trim(); const value = raw !== '' && !Number.isNaN(Number(raw)) ? Number(raw) : raw;
    return [header.trim(), value];
  })));
}

async function loadArtifacts() {
  const responses = await Promise.all(Object.values(ARTIFACTS).map((path) => fetch(path)));
  if (!responses.every((response) => response.ok)) throw new Error('One or more run artifacts could not be loaded. Regenerate artifacts and start a local HTTP server from this project directory.');
  state.leaderboard = parseCSV(await responses[0].text()); state.metrics = await responses[1].json(); state.dataset = await responses[2].json(); state.final = await responses[3].json(); state.cvScores = await responses[4].json();
  state.selectedModel = state.metrics.selected_model || state.leaderboard[0]?.model;
  if (!state.leaderboard.length) throw new Error('leaderboard.csv does not contain any model rows.');
}

function backendLabel(backend) { return backend === 'autogluon' ? 'AutoGluon' : 'sklearn'; }
function metricColumn(metric) { return metric === 'fit_seconds' ? 'cv_fit_seconds_mean' : `cv_${metric}_mean`; }
function metricLabel(metric) { return ({ roc_auc: 'ROC-AUC', balanced_accuracy: 'balanced accuracy', f1: 'malignant F1', sensitivity: 'sensitivity', pr_auc: 'PR-AUC', fit_seconds: 'fit time' }[metric] || metric); }
function isTie(row) { return row.practically_tied === true || row.practically_tied === 1 || String(row.practically_tied).toLowerCase() === 'true'; }
function cvSummary(row, metric) { const mean = row[metricColumn(metric)]; if (mean == null || Number.isNaN(Number(mean))) return '—'; return metric === 'fit_seconds' ? `${seconds(mean)} ± ${seconds(row.cv_fit_seconds_std)}` : `${percent(mean)} ± ${percent(row[`cv_${metric}_std`])}`; }
function ciSummary(row, metric) { return metric === 'fit_seconds' ? cvSummary(row, metric) : `${percent(row[`cv_${metric}_ci_low`])}–${percent(row[`cv_${metric}_ci_high`])}`; }
function visibleRows() {
  const rows = state.leaderboard.filter((row) => state.backendFilter === 'all' || row.backend === state.backendFilter).filter((row) => !state.tieOnly || isTie(row));
  const column = metricColumn(state.sortKey); return rows.sort((a, b) => (state.sortKey === 'fit_seconds' ? 1 : -1) * ((Number(a[column]) || 0) - (Number(b[column]) || 0)));
}
function selectedRow() { return state.leaderboard.find((row) => row.model === state.selectedModel) || state.leaderboard[0]; }

function renderStatus() {
  const status = state.metrics.backend_status || {}; const isAutoGluon = status.autogluon === 'completed'; const agStatus = status.autogluon || 'not attempted';
  $('#backend-title').textContent = isAutoGluon ? 'AutoGluon + sklearn comparison complete' : 'Sklearn fallback comparison complete';
  $('#backend-pill').textContent = isAutoGluon ? 'AutoGluon evaluated' : `AutoGluon ${agStatus}`;
  $('#backend-note').textContent = isAutoGluon ? 'AutoGluon search audit and sklearn folds are recorded separately in the artifacts.' : (state.metrics.autogluon_note || `AutoGluon status: ${agStatus}. The sklearn comparison remains available.`);
  $('#status-explainer-copy').textContent = 'Selection uses development CV only. The selected model’s thresholded final holdout result is shown separately and never ranks the cards.';
  $('#last-updated').textContent = `Seed ${state.metrics.random_seed ?? state.dataset.random_seed} · ${state.metrics.ranking_metric || 'cv_roc_auc_mean'} selection`;
}

function renderSnapshot() {
  const leader = state.leaderboard[0];
  $('#leader-name').textContent = formatName(leader.model); $('#leader-foot').textContent = `Rank #${leader.rank} · ${leader.backend}${isTie(leader) ? ' · practical tie set' : ''}`;
  $('#best-auc').textContent = percent(leader.cv_roc_auc_mean); $('#final-auc').textContent = percent(state.final.roc_auc); $('#model-count').textContent = number(state.leaderboard.length);
  $('#model-count-foot').textContent = `${state.metrics.cv_splits * state.metrics.cv_repeats} fold/repeat records · CV means only`; $('#dataset-caption').textContent = `${formatName(state.dataset.dataset)} · repeated CV + locked holdout`;
  $('#dataset-facts').innerHTML = [['Samples', number(state.dataset.n_samples)], ['Features', number(state.dataset.n_features)], ['Development / final', `${number(state.dataset.development_samples)} / ${number(state.dataset.final_test_samples)}`], ['Final holdout', percent(state.dataset.test_size)], ['Positive class', state.dataset.positive_class?.name || '—'], ['Error cost', 'FN malignant: high']].map(([label, value]) => `<span class="dataset-fact"><strong>${escapeHtml(label)}</strong> ${escapeHtml(value)}</span>`).join('');
}

function renderModelList() {
  const rows = visibleRows(); const maxFit = Math.max(...state.leaderboard.map((row) => Number(row.cv_fit_seconds_mean) || 0), 1);
  $('#model-list').innerHTML = rows.map((row) => {
    const selected = row.model === state.selectedModel; const foldCount = row.cv_fold_count || state.cvScores.models?.[row.model]?.length || 0;
    return `<article class="model-card ${selected ? 'selected' : ''}" data-model="${escapeHtml(row.model)}" tabindex="0" role="button" aria-label="Inspect ${escapeHtml(formatName(row.model))}"><span class="model-rank">${String(row.rank).padStart(2, '0')}</span><div class="model-card-header"><h3 class="model-name">${escapeHtml(formatName(row.model))}</h3><span class="backend-badge">${escapeHtml(backendLabel(row.backend))}</span></div><div class="model-card-badges">${isTie(row) ? '<span class="tie-badge">PRACTICAL TIE</span>' : ''}<span>${foldCount} CV records</span></div><div class="model-metrics"><div class="metric-row"><div class="metric-name"><span>DEV CV ROC-AUC</span><span class="metric-value">${cvSummary(row, 'roc_auc')}</span></div><div class="metric-bar"><div class="metric-fill fill-auc" style="width:${Math.max(0, Number(row.cv_roc_auc_mean) * 100)}%"></div></div></div><div class="metric-row"><div class="metric-name"><span>MALIGNANT SENSITIVITY</span><span class="metric-value">${cvSummary(row, 'sensitivity')}</span></div><div class="metric-bar"><div class="metric-fill fill-accuracy" style="width:${Math.max(0, Number(row.cv_sensitivity_mean) * 100)}%"></div></div></div><div class="metric-row"><div class="metric-name"><span>CV FIT TIME</span><span class="metric-value">${cvSummary(row, 'fit_seconds')}</span></div><div class="metric-bar"><div class="metric-fill fill-time" style="width:${Math.max(3, (Number(row.cv_fit_seconds_mean) / maxFit) * 100)}%"></div></div></div></div></article>`;
  }).join('') || '<div class="loading-card">No models match this filter.</div>';
  document.querySelectorAll('.model-card').forEach((card) => { const choose = () => selectModel(card.dataset.model); card.addEventListener('click', choose); card.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); choose(); } }); });
}

function renderDetail() {
  const row = selectedRow(); if (!row) return; const folds = state.cvScores.models?.[row.model] || []; const rocValues = folds.map((fold) => Number(fold.roc_auc)).filter(Number.isFinite); const holdoutSelected = row.model === state.final.model;
  $('#detail-title').textContent = formatName(row.model); $('#model-select').value = row.model;
  const holdout = holdoutSelected ? `<div class="holdout-result"><span class="detail-backend">LOCKED FINAL HOLDOUT · EVALUATED ONCE</span><div class="holdout-grid"><div><span>ROC-AUC</span><strong>${percent(state.final.roc_auc)}</strong></div><div><span>SENSITIVITY</span><strong>${percent(state.final.sensitivity)}</strong></div><div><span>SPECIFICITY</span><strong>${percent(state.final.specificity)}</strong></div><div><span>PR-AUC</span><strong>${percent(state.final.pr_auc)}</strong></div><div><span>PRECISION / NPV</span><strong>${percent(state.final.precision)} / ${percent(state.final.npv)}</strong></div><div><span>CONFUSION MATRIX</span><strong>${state.final.confusion_matrix ? `TN ${state.final.confusion_matrix.tn} · FP ${state.final.confusion_matrix.fp} · FN ${state.final.confusion_matrix.fn} · TP ${state.final.confusion_matrix.tp}` : '—'}</strong></div></div></div>` : '<p class="detail-note">No final holdout score is shown for non-selected models; the holdout is reserved for the selected model.</p>';
  $('#model-detail').innerHTML = `<span class="detail-backend">${escapeHtml(backendLabel(row.backend).toUpperCase())} · RANK #${row.rank} · ${isTie(row) ? 'PRACTICAL TIE SET' : 'LEADERBOARD ROW'}</span><div class="detail-score"><strong>${percent(row.cv_roc_auc_mean)}</strong><span>DEV CV ROC-AUC<br />SELECTION SIGNAL<br /><small>95% CI ${ciSummary(row, 'roc_auc')}</small></span></div><div class="detail-stat-grid"><div class="detail-stat"><span>MALIGNANT SENSITIVITY</span><strong>${cvSummary(row, 'sensitivity')}</strong></div><div class="detail-stat"><span>SPECIFICITY</span><strong>${cvSummary(row, 'specificity')}</strong></div><div class="detail-stat"><span>PR-AUC</span><strong>${cvSummary(row, 'pr_auc')}</strong></div><div class="detail-stat"><span>THRESHOLD</span><strong>${Number(row.decision_threshold).toFixed(3)}</strong></div><div class="detail-stat"><span>FIT TIME</span><strong>${cvSummary(row, 'fit_seconds')}</strong></div><div class="detail-stat"><span>FOLD RANGE</span><strong>${rocValues.length ? `${percent(Math.min(...rocValues))}–${percent(Math.max(...rocValues))}` : '—'}</strong></div></div><p class="detail-note">Threshold selected from development-only out-of-fold predictions by malignant F1. ${isTie(row) ? 'This score is within the declared practical tie tolerance of the leader.' : 'This row is not marked as practically tied with the leader.'}</p>${holdout}`;
}

function selectModel(model) { state.selectedModel = model; renderModelList(); renderDetail(); }
function renderChart() {
  const rows = visibleRows(); const column = metricColumn(state.sortKey); const values = rows.map((row) => Number(row[column]) || 0); const max = Math.max(...values, 1); const fitValues = state.leaderboard.map((row) => Number(row.cv_fit_seconds_mean) || 0); const maxFit = Math.max(...fitValues, 1);
  $('#comparison-chart').innerHTML = rows.map((row) => { const value = Number(row[column]) || 0; const width = state.sortKey === 'fit_seconds' ? (value / max) * 100 : value * 100; return `<div class="chart-row"><span class="chart-label">${escapeHtml(formatName(row.model))}</span><div class="chart-bars"><div class="chart-bar chart-auc" title="${escapeHtml(metricLabel(state.sortKey))}: ${escapeHtml(cvSummary(row, state.sortKey))}"><span style="width:${Math.max(2, width)}%"></span></div><div class="chart-bar chart-accuracy" title="CV fit time: ${escapeHtml(cvSummary(row, 'fit_seconds'))}"><span style="width:${Math.max(2, (Number(row.cv_fit_seconds_mean) / maxFit) * 100)}%"></span></div></div><span class="chart-value">${state.sortKey === 'fit_seconds' ? seconds(value) : percent(value)}</span></div>`; }).join('');
  $('#chart-caption').textContent = state.sortKey === 'fit_seconds' ? 'Lower CV fit time is better; quality remains visible in the model detail.' : `Higher ${metricLabel(state.sortKey)} is better; bars show ${metricLabel(state.sortKey)} and relative CV fit time.`;
}
function renderControls() { $('#sort-select').value = state.sortKey; $('#backend-filter').value = state.backendFilter; $('#tie-filter').checked = state.tieOnly; $('#explorer-note').textContent = `${visibleRows().length} of ${state.leaderboard.length} models · ${metricLabel(state.sortKey)} lens · selection remains ${state.metrics.ranking_metric || 'development-CV ROC-AUC'}.`; }
function populateControls() {
  const backends = [...new Set(state.leaderboard.map((row) => row.backend))]; $('#backend-filter').innerHTML = '<option value="all">All backends</option>' + backends.map((backend) => `<option value="${escapeHtml(backend)}">${escapeHtml(backendLabel(backend))}</option>`).join('');
  $('#sort-select').addEventListener('change', (event) => { state.sortKey = event.target.value; renderControls(); renderModelList(); renderDetail(); renderChart(); }); $('#backend-filter').addEventListener('change', (event) => { state.backendFilter = event.target.value; renderControls(); renderModelList(); renderDetail(); renderChart(); }); $('#tie-filter').addEventListener('change', (event) => { state.tieOnly = event.target.checked; renderControls(); renderModelList(); renderDetail(); renderChart(); });
  const selector = $('#model-select'); selector.innerHTML = state.leaderboard.map((row) => `<option value="${escapeHtml(row.model)}">${escapeHtml(formatName(row.model))}</option>`).join(''); selector.disabled = false; selector.addEventListener('change', () => selectModel(selector.value));
}
function showError(error) { const toast = $('#error-toast'); toast.textContent = error.message; toast.hidden = false; $('#last-updated').textContent = 'Artifact load failed'; $('#backend-title').textContent = 'Unable to read run status'; $('#backend-pill').textContent = 'Needs local server'; }
async function init() { try { await loadArtifacts(); renderStatus(); renderSnapshot(); populateControls(); renderControls(); renderModelList(); renderDetail(); renderChart(); } catch (error) { showError(error); } }
init();
