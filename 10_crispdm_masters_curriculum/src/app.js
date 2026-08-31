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

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' })[char]);
const pretty = (value) => typeof value === 'number' ? value.toLocaleString() : esc(value);
const pct = (value) => `${(Number(value) * 100).toFixed(1)}%`;
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
  const baseline = evaluation.majority_baseline;
  const passed = Boolean(baseline && baseline.accuracy_delta > 0);
  $('#threshold-stat').textContent = 'beats majority CV baseline';
  $('#evaluation-headline').textContent = passed ? 'Model beats the baseline.' : 'Model needs another pass.';
  $('.check-badge').textContent = passed ? '✓ BASELINE+' : '↺ REVIEW';
  $('.check-badge').classList.toggle('review-badge', !passed);
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
  if (key === 'modeling') return `<div class="detail-grid">${textItem('Selected model', model.selected_model, true)}${textItem('Protocol', model.selection_protocol, true)}${textItem('Selection metric', model.selection_metric)}${item('Candidates', list(model.candidates.map((candidate) => `${candidate.name}: ${pct(candidate.cv_accuracy_mean)}`)), true)}<div class="teaching-callout wide">CV touches training rows only; the fixed holdout stays out of model selection.</div></div>`;
  if (key === 'evaluation') return `<div class="detail-grid">${strongItem('Accuracy', pct(evaluation.accuracy))}${strongItem('Holdout rows', pretty(evaluation.total))}${textItem('95% Wilson interval', `${pct(evaluation.accuracy_95_wilson_interval[0])}–${pct(evaluation.accuracy_95_wilson_interval[1])}`)}${textItem('Readout', `${evaluation.correct}/${evaluation.total} correct on this fixed holdout; this is split-specific evidence.`, true)}${item('Per-class F1', list(data.classes.map((name) => `${name}: ${pct(evaluation.classification_report[name]['f1-score'])}`)), true)}</div>`;
  return `<div class="detail-grid">${textItem('Status', deployment.status, true)}${textItem('Inference', deployment.inference_command, true)}${textItem('Claim boundary', deployment.claim_boundary, true)}${item('Monitor', list(deployment.monitoring_plan.map((entry) => `${entry.signal} · ${entry.window}`)), true)}<div class="teaching-callout wide">The bundle is usable for local inference, but external validation is still required before production approval.</div></div>`;
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
  $('#confusion-matrix').innerHTML = `<table class="matrix"><thead><tr><th></th>${labels.map((label) => `<th scope="col">${esc(label.slice(0, 5))}</th>`).join('')}</tr></thead><tbody>${matrix.map((row, rowIndex) => `<tr><th class="row-label" scope="row">${esc(labels[rowIndex].slice(0, 5))}</th>${row.map((value, colIndex) => `<td class="${rowIndex === colIndex ? 'correct' : ''}">${value}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  const scores = report.evaluation.classification_report;
  $('#class-scores').innerHTML = labels.map((label) => `<div class="class-score"><strong>${esc(label)}</strong><small>F1 ${pct(scores[label]['f1-score'])} · n=${scores[label].support}</small></div>`).join('');
}

function renderFeatures() { $('#feature-list').innerHTML = list(report.data_understanding.features, 'feature-list'); }
function selectPhase(key) { if (!phaseMeta[key]) return; activePhase = key; renderPhaseCards(); renderDetail(); }

async function loadReport() {
  try {
    const response = await fetch('artifacts/crispdm_report.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    report = await response.json();
    renderStats(); renderPhaseCards(); renderDetail(); renderMatrix(); renderFeatures();
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
  const copyButton = event.target.closest('[data-copy], #copy-command');
  if (copyButton) {
    const command = copyButton.dataset.copy || 'python3 src/crispdm_demo.py';
    if (navigator.clipboard) navigator.clipboard.writeText(command).then(() => showToast('Command copied')).catch(() => showToast(command));
    else showToast(command);
  }
});

loadReport();
