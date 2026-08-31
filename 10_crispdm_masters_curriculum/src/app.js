const phaseMeta = {
  business_understanding: { number: '01', label: 'FRAME THE DECISION', title: 'Business understanding', summary: 'Start with a decision worth supporting, not a model worth showing.', short: 'Frame the decision' },
  data_understanding: { number: '02', label: 'MEET THE EVIDENCE', title: 'Data understanding', summary: 'Know what the dataset can say before asking it to predict.', short: 'Meet the evidence' },
  data_preparation: { number: '03', label: 'MAKE IT READY', title: 'Data preparation', summary: 'Build a clean, reproducible path from raw measurements to features.', short: 'Make it ready' },
  modeling: { number: '04', label: 'LEARN A PATTERN', title: 'Modeling', summary: 'Choose a transparent baseline that turns the prepared data into a signal.', short: 'Learn a pattern' },
  evaluation: { number: '05', label: 'TEST THE CLAIM', title: 'Evaluation', summary: 'Measure the model against data it did not get to see during training.', short: 'Test the claim' },
  deployment: { number: '06', label: 'CARRY IT FORWARD', title: 'Deployment', summary: 'Name the next operational step—and the signals that keep it honest.', short: 'Carry it forward' },
};
const phaseKeys = Object.keys(phaseMeta);
let report = null;
let activePhase = 'business_understanding';
let selectedModelName = null;
let selectedBaselineName = null;
let selectedMetric = null;
let selectedMatrixCell = null;

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' })[char]);
const pretty = (value) => typeof value === 'number' ? value.toLocaleString() : esc(value);
const pct = (value) => `${(Number(value) * 100).toFixed(1)}%`;
const shortHash = (value) => value ? `${String(value).slice(0, 12)}…` : 'not recorded';
const list = (items, className = 'chip-list') => `<div class="${className}">${items.map((item) => `<span class="chip">${esc(item)}</span>`).join('')}</div>`;

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove('show'), 1800);
}

function renderStats() {
  const data = report.data_understanding;
  const prep = report.data_preparation;
  const evaluation = report.evaluation;
  $('#accuracy-stat').textContent = pct(evaluation.accuracy);
  $('#ring-value').textContent = pct(evaluation.accuracy);
  $('#rows-stat').textContent = pretty(data.rows);
  $('#test-stat').textContent = pretty(prep.test_rows);
  $('#missing-stat').textContent = pretty(data.missing_values);
  $('#dataset-name').textContent = data.dataset;
  const passed = Boolean(report.modeling && report.modeling.beats_baseline_in_cv);
  const holdoutDelta = evaluation.majority_baseline ? `holdout Δ ${evaluation.majority_baseline.accuracy_delta >= 0 ? '+' : ''}${pct(evaluation.majority_baseline.accuracy_delta)}` : 'descriptive readout';
  $('#threshold-stat').textContent = holdoutDelta;
  $('#evaluation-headline').textContent = passed ? 'Model beats the baseline.' : 'Model needs another pass.';
  $('.check-badge').textContent = passed ? '✓ CV GATE PASS' : '↺ CV GATE REVIEW';
  $('.check-badge').classList.toggle('review-badge', !passed);
  $('#gate-explanation').textContent = passed
    ? 'Curriculum gate: selected model mean repeated-CV accuracy is above the majority baseline (training rows only).'
    : 'Curriculum gate: selected model did not beat the majority baseline in training-only repeated CV.';
}

function renderPhaseCards() {
  $('#phase-cards').innerHTML = phaseKeys.map((key) => {
    const meta = phaseMeta[key];
    const detail = report[key] || {};
    const hint = key === 'business_understanding' ? 'bounded classroom decision' : key === 'data_understanding' ? `${detail.rows} rows · ${detail.missing_values} missing` : key === 'data_preparation' ? `${detail.train_rows} train · ${detail.test_rows} test` : key === 'modeling' ? `${detail.selected_model} · CV selected` : key === 'evaluation' ? `${pct(detail.accuracy)} · ${detail.total} holdout` : 'validated local bundle';
    return `<button class="phase-card ${key === activePhase ? 'active' : ''}" data-phase="${key}" role="listitem" aria-pressed="${key === activePhase}"><span class="phase-card-index">${meta.number} / 06</span><h3>${meta.short}</h3><p>${esc(hint)}</p></button>`;
  }).join('');
}

function item(label, value, wide = false) { return `<div class="detail-item ${wide ? 'wide' : ''}"><label>${esc(label)}</label>${value}</div>`; }
function textItem(label, value, wide = false) { return item(label, `<p>${esc(value)}</p>`, wide); }
function strongItem(label, value, wide = false) { return item(label, `<strong>${esc(value)}</strong>`, wide); }

function detailMarkup(key) {
  const data = report.data_understanding;
  const business = report.business_understanding;
  const prep = report.data_preparation;
  const model = report.modeling;
  const evaluation = report.evaluation;
  const deployment = report.deployment;
  if (key === 'business_understanding') return `<div class="detail-grid">${textItem('Objective', business.objective, true)}${textItem('Decision', business.decision, true)}${textItem('Success criteria', business.success_criteria, true)}${item('Stakeholders', list(business.stakeholders))}${textItem('Claim boundary', business.error_costs, true)}</div>`;
  if (key === 'data_understanding') return `<div class="detail-grid">${strongItem('Dataset', data.dataset)}${strongItem('Rows', pretty(data.rows))}${strongItem('Classes', data.classes.length)}${strongItem('Missing values', pretty(data.missing_values))}${strongItem('Duplicate feature rows', pretty(data.quality_checks.duplicate_feature_rows))}${item('Features', list(data.features), true)}${item('Class balance', list(Object.entries(data.class_counts).map(([name, count]) => `${name}: ${count}`)), true)}${textItem('Content hash', data.content_sha256, true)}</div>`;
  if (key === 'data_preparation') return `<div class="detail-grid">${strongItem('Training rows', pretty(prep.train_rows))}${strongItem('Test rows', pretty(prep.test_rows))}${textItem('Split strategy', prep.split)}${textItem('Preprocessing', prep.preprocessing, true)}<div class="teaching-callout wide">Scaling is fit inside the pipeline on training data only, keeping the holdout honest.</div></div>`;
  if (key === 'modeling') return `<div class="detail-grid">${textItem('Selected model', model.selected_model, true)}${textItem('Protocol', model.selection_protocol, true)}${textItem('Selection metric', model.selection_metric)}${strongItem('CV gate', model.beats_baseline_in_cv ? 'PASS · above majority baseline' : 'REVIEW · at or below majority baseline', true)}${item('Candidates', list(model.candidates.map((candidate) => `${candidate.name}: ${pct(candidate.cv_accuracy_mean)}`)), true)}<div class="teaching-callout wide">CV touches training rows only; the fixed holdout stays out of model selection. Use the explorer below to inspect every fold score.</div></div>`;
  if (key === 'evaluation') return `<div class="detail-grid">${strongItem('Accuracy', pct(evaluation.accuracy))}${strongItem('Holdout rows', pretty(evaluation.total))}${textItem('95% Wilson interval', `${pct(evaluation.accuracy_95_wilson_interval[0])}–${pct(evaluation.accuracy_95_wilson_interval[1])}`)}${textItem('Readout', `${evaluation.correct}/${evaluation.total} correct on this fixed holdout; this is split-specific evidence.`, true)}${item('Per-class F1', list(data.classes.map((name) => `${name}: ${pct(evaluation.classification_report[name]['f1-score'])}`)), true)}</div>`;
  return `<div class="detail-grid">${textItem('Status', deployment.status, true)}${textItem('Inference', deployment.inference_command, true)}${textItem('Validation semantics', deployment.validation_semantics.holdout_readout, true)}${textItem('Claim boundary', deployment.claim_boundary, true)}${item('Monitor', list(deployment.monitoring_plan.map((entry) => `${entry.signal} · ${entry.window}`)), true)}<div class="teaching-callout wide">The bundle is usable for local inference, but external validation is still required before production approval.</div></div>`;
}

function renderDetail() {
  const meta = phaseMeta[activePhase];
  $('#detail-index').textContent = `${meta.number} / 06`;
  $('#detail-tag').textContent = meta.label;
  $('#detail-title').textContent = meta.title;
  $('#detail-summary').textContent = meta.summary;
  $('#detail-content').innerHTML = detailMarkup(activePhase);
  document.querySelectorAll('[data-phase]').forEach((button) => {
    const selected = button.dataset.phase === activePhase;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', selected);
  });
}

function renderMatrix() {
  const labels = report.data_understanding.classes;
  const matrix = report.evaluation.confusion_matrix;
  $('#confusion-matrix').innerHTML = `<table class="matrix"><caption>Rows are actual classes; columns are predicted. Select a cell to inspect its holdout rows.</caption><thead><tr><th></th>${labels.map((label) => `<th scope="col">${esc(label.slice(0, 5))}</th>`).join('')}</tr></thead><tbody>${matrix.map((row, rowIndex) => `<tr><th class="row-label" scope="row">${esc(labels[rowIndex].slice(0, 5))}</th>${row.map((value, colIndex) => `<td class="${rowIndex === colIndex ? 'correct' : ''}"><button type="button" class="matrix-cell" data-matrix-row="${rowIndex}" data-matrix-col="${colIndex}" aria-label="${esc(labels[rowIndex])} predicted as ${esc(labels[colIndex])}: ${value} row${value === 1 ? '' : 's'}">${value}</button></td>`).join('')}</tr>`).join('')}</tbody></table>`;
  const scores = report.evaluation.classification_report;
  $('#class-scores').innerHTML = labels.map((label) => `<div class="class-score"><strong>${esc(label)}</strong><small>F1 ${pct(scores[label]['f1-score'])} · n=${scores[label].support}</small></div>`).join('');
  $('#failure-cases').innerHTML = (report.evaluation.failure_cases || []).length
    ? report.evaluation.failure_cases.map((item) => `<button type="button" class="failure-link" data-matrix-row="${labels.indexOf(item.actual_class)}" data-matrix-col="${labels.indexOf(item.predicted_class)}"><strong>Holdout row ${item.row_number_in_holdout}</strong><span>${esc(item.actual_class)} → ${esc(item.predicted_class)}</span></button>`).join('')
    : '<p class="empty-detail">No failure cases recorded.</p>';
  renderMatrixSelection();
}

function renderFeatures() { $('#feature-list').innerHTML = list(report.data_understanding.features, 'feature-list'); }
function selectPhase(key) { if (!phaseMeta[key]) return; activePhase = key; renderPhaseCards(); renderDetail(); }

function candidates() { return report?.modeling?.candidates || []; }
function candidateByName(name) { return candidates().find((candidate) => candidate.name === name) || candidates()[0]; }
function candidateLabel(candidate) { return candidate ? `${candidate.name} · ${candidate.algorithm}` : 'Unavailable'; }

function renderExplorerControls() {
  const availableMetrics = report.modeling.available_metrics || [report.modeling.selection_metric];
  selectedModelName = selectedModelName || report.modeling.selected_model;
  selectedBaselineName = selectedBaselineName || 'majority_class';
  selectedMetric = selectedMetric || report.modeling.selection_metric;
  $('#model-select').innerHTML = candidates().map((candidate) => `<option value="${esc(candidate.name)}">${esc(candidateLabel(candidate))}</option>`).join('');
  $('#baseline-select').innerHTML = candidates().map((candidate) => `<option value="${esc(candidate.name)}">${esc(candidateLabel(candidate))}</option>`).join('');
  $('#metric-select').innerHTML = availableMetrics.map((metric) => `<option value="${esc(metric)}">${esc(metric)}</option>`).join('');
  $('#model-select').value = selectedModelName;
  $('#baseline-select').value = selectedBaselineName;
  $('#metric-select').value = selectedMetric;
  renderExplorer();
}

function renderExplorer() {
  const selected = candidateByName(selectedModelName);
  const baseline = candidateByName(selectedBaselineName);
  const metric = selectedMetric || report.modeling.selection_metric;
  if (!selected || !baseline) return;
  const scores = selected.cv_scores || [];
  const maxScore = Math.max(...scores, 1);
  const rows = candidates().map((candidate) => {
    const isSelected = candidate.name === selected.name;
    const isBaseline = candidate.name === baseline.name;
    return `<tr class="${isSelected ? 'selected-row' : ''}"><th scope="row"><button type="button" class="table-model-button" data-model-choice="${esc(candidate.name)}">${esc(candidate.name)}</button>${isSelected ? '<span class="table-tag">inspected</span>' : ''}${isBaseline ? '<span class="table-tag baseline-tag">baseline</span>' : ''}</th><td>${esc(candidate.algorithm)}</td><td><strong>${pct(candidate.cv_accuracy_mean)}</strong> <span class="muted">± ${pct(candidate.cv_accuracy_std)}</span></td><td>${pct(candidate.cv_accuracy_min)}–${pct(candidate.cv_accuracy_max)}</td></tr>`;
  }).join('');
  $('#model-comparison').innerHTML = `<table class="comparison-table"><caption>${esc(metric)} on ${esc(report.modeling.selection_protocol)}.</caption><thead><tr><th scope="col">Candidate</th><th scope="col">Estimator</th><th scope="col">Mean ± SD</th><th scope="col">Observed range</th></tr></thead><tbody>${rows}</tbody></table>`;
  $('#score-distribution').innerHTML = scores.map((score, index) => `<div class="score-bar-row"><span>fold ${index + 1}</span><div class="score-bar-track"><i style="width:${Math.max(4, Number(score) * 100 / maxScore)}%"></i></div><strong>${pct(score)}</strong></div>`).join('');
  const delta = selected.cv_accuracy_mean - baseline.cv_accuracy_mean;
  $('#explorer-summary').innerHTML = `<strong>${esc(candidateLabel(selected))}</strong> scores ${pct(selected.cv_accuracy_mean)} mean CV accuracy, ${delta >= 0 ? '+' : ''}${pct(delta)} vs <strong>${esc(baseline.name)}</strong>. <span>${selected.name === report.modeling.selected_model ? 'This is the fitted artifact used for the holdout readout.' : 'This candidate is not the fitted artifact; no holdout claim is attached here.'}</span>`;
}

function casesForCell(rowIndex, colIndex) {
  return (report.evaluation.holdout_cases || []).filter((item) => {
    const row = report.data_understanding.classes.indexOf(item.actual_class);
    const col = report.data_understanding.classes.indexOf(item.predicted_class);
    return row === rowIndex && col === colIndex;
  });
}

function renderMatrixSelection() {
  const labels = report.data_understanding.classes;
  const chosen = selectedMatrixCell || { row: 0, col: 0 };
  const cases = casesForCell(chosen.row, chosen.col);
  document.querySelectorAll('.matrix-cell').forEach((button) => {
    button.classList.toggle('active', Number(button.dataset.matrixRow) === chosen.row && Number(button.dataset.matrixCol) === chosen.col);
  });
  $('#error-detail').innerHTML = `<div class="error-detail-heading"><strong>${esc(labels[chosen.row])} → ${esc(labels[chosen.col])}</strong><span>${cases.length} holdout row${cases.length === 1 ? '' : 's'}</span></div>${cases.length ? `<div class="case-list">${cases.map((item) => `<article class="case-item ${item.correct ? 'case-correct' : 'case-failure'}"><div><strong>Holdout row ${item.row_number_in_holdout} · dataset row ${item.dataset_row_index}</strong><span>${item.correct ? 'Correct' : 'Failure'} · predicted ${esc(item.predicted_probability == null ? 'probability unavailable' : pct(item.predicted_probability))}</span></div><dl>${Object.entries(item.features).map(([name, value]) => `<div><dt>${esc(name)}</dt><dd>${Number(value).toFixed(1)} cm</dd></div>`).join('')}</dl></article>`).join('')}</div>` : '<p class="empty-detail">No holdout rows land in this cell.</p>'}<p class="claim-note">Features and rows come from the locked holdout artifact; this inspection does not change the pass gate.</p>`;
}

function renderArtifacts() {
  const artifacts = report.artifacts || {};
  $('#artifact-list').innerHTML = Object.entries(artifacts).map(([name, metadata]) => `<li><a href="artifacts/${encodeURIComponent(name)}" target="_blank" rel="noreferrer">${esc(name)}</a><code title="${esc(metadata.sha256)}">${esc(shortHash(metadata.sha256))}</code></li>`).join('');
  $('#model-identity').innerHTML = `<div><span>Bundle schema</span><strong>${esc(report.deployment.bundle_schema_version || 'unknown')} · validated</strong></div><div><span>Config fingerprint</span><code title="${esc(report.modeling.model_configuration_fingerprint)}">${esc(shortHash(report.modeling.model_configuration_fingerprint))}</code></div><div><span>Fitted fingerprint</span><code title="${esc(report.modeling.fitted_model_fingerprint)}">${esc(shortHash(report.modeling.fitted_model_fingerprint))}</code></div><div><span>Dataset SHA-256</span><code title="${esc(report.data_understanding.content_sha256)}">${esc(shortHash(report.data_understanding.content_sha256))}</code></div>`;
}

function renderInferenceForm() {
  const contract = report.deployment.input_contract;
  $('#inference-fields').innerHTML = contract.feature_names.map((name, index) => `<label><span>${esc(name)} <small>(${esc(contract.units)})</small></span><input name="${esc(name)}" type="number" inputmode="decimal" step="any" min="${contract.allowed_range_per_feature[0]}" max="${contract.allowed_range_per_feature[1]}" value="${[5.1, 3.5, 1.4, 0.2][index] ?? ''}" required></label>`).join('');
  $('#inference-contract-note').textContent = `Named fields are canonicalised to the saved order. Each value must be a finite numeric ${contract.units} measurement in [${contract.allowed_range_per_feature.join(', ')}]; invalid, missing, or extra named input is rejected. Positional input is never silently reordered, but plausible swaps require named metadata to detect. The browser checks the contract only—model execution remains local via the CLI.`;
}

async function loadReport() {
  try {
    const response = await fetch('artifacts/crispdm_report.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    report = await response.json();
    renderStats(); renderPhaseCards(); renderDetail(); renderMatrix(); renderFeatures(); renderExplorerControls(); renderArtifacts(); renderInferenceForm();
    $('#report-status').innerHTML = '<span class="status-dot"></span> Report connected';
  } catch (error) {
    $('#report-status').innerHTML = '<span class="status-dot" style="background:#dc735d"></span> Report unavailable';
    $('#detail-content').innerHTML = '<div class="teaching-callout">Start a local server from this project directory to let the browser load the JSON report: <code>python -m http.server 8000</code>.</div>';
    console.error('Could not load crispdm_report.json', error);
  }
}

document.addEventListener('click', (event) => {
  const phaseButton = event.target.closest('[data-phase]');
  if (phaseButton) selectPhase(phaseButton.dataset.phase);
  const modelChoice = event.target.closest('[data-model-choice]');
  if (modelChoice) {
    selectedModelName = modelChoice.dataset.modelChoice;
    $('#model-select').value = selectedModelName;
    renderExplorer();
  }
  const matrixCell = event.target.closest('[data-matrix-row]');
  if (matrixCell) {
    selectedMatrixCell = { row: Number(matrixCell.dataset.matrixRow), col: Number(matrixCell.dataset.matrixCol) };
    renderMatrixSelection();
  }
  const copyButton = event.target.closest('[data-copy], #copy-command');
  if (copyButton) {
    const command = copyButton.dataset.copy || 'python3 src/crispdm_demo.py';
    if (navigator.clipboard) navigator.clipboard.writeText(command).then(() => showToast('Command copied')).catch(() => showToast(command));
    else showToast(command);
  }
});

document.addEventListener('change', (event) => {
  if (event.target.id === 'model-select') selectedModelName = event.target.value;
  if (event.target.id === 'baseline-select') selectedBaselineName = event.target.value;
  if (event.target.id === 'metric-select') selectedMetric = event.target.value;
  if (['model-select', 'baseline-select', 'metric-select'].includes(event.target.id)) renderExplorer();
});

document.addEventListener('submit', (event) => {
  if (!event.target.matches('#inference-form')) return;
  event.preventDefault();
  const contract = report.deployment.input_contract;
  const values = Object.fromEntries(new FormData(event.target).entries());
  const errors = [];
  const ordered = contract.feature_names.map((name) => {
    const raw = values[name];
    const value = Number(raw);
    if (raw === '' || !Number.isFinite(value)) errors.push(`${name}: finite numeric value required`);
    else if (value < contract.allowed_range_per_feature[0] || value > contract.allowed_range_per_feature[1]) errors.push(`${name}: must be within [${contract.allowed_range_per_feature.join(', ')}] ${contract.units}`);
    return value;
  });
  const result = $('#inference-result');
  if (errors.length) {
    result.className = 'inference-result invalid';
    result.innerHTML = `<strong>Contract rejected</strong><span>${errors.map(esc).join('<br>')}</span>`;
    return;
  }
  result.className = 'inference-result valid';
  result.innerHTML = `<strong>Contract accepted</strong><span>Canonical payload ready in saved order: <code>${esc(JSON.stringify(ordered))}</code>. Run the local inference command shown above to execute the fitted bundle.</span>`;
});

loadReport();
