const artifactBase = '../artifacts/';
const $ = (selector) => document.querySelector(selector);
let auditArtifact = null;
let errorRows = [];

function escapeHtml(value) {
  return String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function formatPercent(value) {
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Number(value).toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function setKpis(metrics) {
  const holdoutShare = formatPercent(metrics.test_fraction ?? (metrics.test_rows / metrics.retained_rows));
  const baseline = metrics.baselines?.global_mean;
  const baselineNote = baseline ? `Global-mean baseline MAE: ${formatNumber(baseline.mae_minutes, 3)} min` : 'Synthetic holdout';
  $('#kpi-grid').innerHTML = `
    <article class="kpi-card kpi-featured"><span class="kpi-label">R²</span><strong>${formatNumber(metrics.r2, 3)}</strong><span>coefficient of determination · synthetic holdout</span></article>
    <article class="kpi-card"><span class="kpi-label">Mean absolute error</span><strong>${formatNumber(metrics.mae_minutes, 3)}</strong><span>minutes per trip · ${baselineNote}</span></article>
    <article class="kpi-card"><span class="kpi-label">RMSE</span><strong>${formatNumber(metrics.rmse_minutes, 3)}</strong><span>minutes · chronological holdout</span></article>
    <article class="kpi-card"><span class="kpi-label">Holdout rows</span><strong>${formatNumber(metrics.test_rows)}</strong><span>${formatNumber(metrics.test_rows)} of ${formatNumber(metrics.retained_rows)} retained · ${holdoutShare}</span></article>`;
  $('#last-updated').textContent = `Synthetic smoke test · run ${metrics.run_id || 'unidentified'}`;
}

const severityRank = { critical: 3, warning: 2, info: 1 };
function categorySeverity(category, findings) {
  const finding = findings.filter((item) => item.category === category).sort((a, b) => (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0))[0];
  return finding?.severity || null;
}

function signalFor(value, severity) {
  if (!value) return '<span class="signal signal-good">Clean</span>';
  if (severity === 'critical') return '<span class="signal signal-critical">Block</span>';
  if (severity === 'warning') return '<span class="signal signal-watch">Review</span>';
  return '<span class="signal signal-info">Observe</span>';
}

function renderFindings() {
  if (!auditArtifact) return;
  const severity = $('#audit-severity').value;
  const status = $('#audit-status').value;
  const query = $('#audit-search').value.trim().toLowerCase();
  const findings = (auditArtifact.findings || []).filter((finding) => {
    const searchable = [finding.category, finding.field, finding.trip_id, finding.action, finding.status].join(' ').toLowerCase();
    return (severity === 'all' || finding.severity === severity) && (status === 'all' || finding.status === status) && (!query || searchable.includes(query));
  });
  $('#finding-list').innerHTML = findings.length ? findings.map((finding) => `
    <details class="finding-item">
      <summary><span class="finding-severity finding-${escapeHtml(finding.severity)}">${escapeHtml(finding.severity)}</span><strong>${escapeHtml(finding.category)}</strong><span>${finding.trip_id === null ? 'schema' : `trip ${escapeHtml(finding.trip_id)}`}</span></summary>
      <div class="finding-meta"><span><b>Field</b> ${escapeHtml(finding.field || '—')}</span><span><b>Row</b> ${escapeHtml(finding.row_index ?? '—')}</span><span><b>Status</b> ${escapeHtml(finding.status)}</span><span><b>Action</b> ${escapeHtml(finding.action)}</span></div>
    </details>`).join('') : '<p class="empty-state">No findings match these filters.</p>';
  $('#finding-list').dataset.count = findings.length;
}

function setAudit(audit) {
  auditArtifact = audit;
  const categories = audit.finding_counts || [];
  const findings = audit.findings || [];
  const activeCategories = categories.filter((entry) => entry.count > 0).length;
  $('#audit-table').innerHTML = `<div class="audit-row audit-header" role="row"><span>Check</span><span>Observed</span><span>Signal</span></div>${categories.map((entry) => `<div class="audit-row" role="row"><span>${escapeHtml(entry.label)}</span><strong>${formatNumber(entry.count)}</strong>${signalFor(entry.count, categorySeverity(entry.category, findings))}</div>`).join('')}`;
  $('#audit-summary').innerHTML = `<span class="audit-summary-icon">${findings.length ? '!' : '✓'}</span><div><strong>${findings.length ? `${formatNumber(findings.length)} findings across ${formatNumber(activeCategories)} categories` : 'No audit findings'}</strong><span>${formatNumber(audit.rows)} raw rows · row-level details available below</span></div>`;
  renderFindings();
}

function identityValue(label, value, code = false) {
  return `<div class="identity-card"><span>${escapeHtml(label)}</span><strong${code ? ' class="identity-code"' : ''}>${escapeHtml(value ?? '—')}</strong></div>`;
}

function setManifest(manifest) {
  const config = manifest.configuration || {};
  const source = manifest.source || {};
  const population = manifest.population || {};
  const runtime = manifest.runtime || {};
  const ranges = population.time_ranges || {};
  $('#run-identity').innerHTML = [
    identityValue('Run ID', manifest.run_id, true),
    identityValue('Git revision', source.git_revision === 'unavailable' ? 'unavailable' : String(source.git_revision).slice(0, 12), true),
    identityValue('Seed / rows', `${config.seed ?? '—'} / ${config.rows_argument ?? '—'}`),
    identityValue('Population', `${population.retained_rows ?? '—'} retained · ${population.excluded_rows ?? '—'} excluded`),
    identityValue('Time boundary', `${ranges.train_end || '—'} → ${ranges.holdout_start || '—'}`),
    identityValue('Runtime', `${runtime.python || '—'} · ${runtime.packages?.['scikit-learn'] || 'sklearn —'}`),
    identityValue('Data hash', String(source.data_hash_sha256 || '—').slice(0, 16), true),
    identityValue('Source hash', String(source.source_hash_sha256 || '—').slice(0, 16), true),
    identityValue('Artifact integrity', `${Object.keys(manifest.artifact_hashes_sha256 || {}).length} files hashed at generation`),
  ].join('');
}

function inlineMarkdown(text) {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`(.+?)`/g, '<code>$1</code>');
}

function renderReport(markdown) {
  const lines = markdown.split(/\r?\n/);
  const output = [];
  let listOpen = false;
  const closeList = () => { if (listOpen) { output.push('</ul>'); listOpen = false; } };
  lines.forEach((line) => {
    if (line.startsWith('# ')) return;
    if (line.startsWith('## ')) { closeList(); output.push(`<h3>${inlineMarkdown(line.slice(3))}</h3>`); return; }
    if (line.startsWith('- ')) { if (!listOpen) { output.push('<ul>'); listOpen = true; } output.push(`<li>${inlineMarkdown(line.slice(2))}</li>`); return; }
    if (!line.trim()) { closeList(); return; }
    closeList(); output.push(`<p>${inlineMarkdown(line)}</p>`);
  });
  closeList();
  $('#report-panel').innerHTML = output.join('');
}

const sliceLabels = { pickup_hour: 'Pickup hour', weekday: 'Weekday', duration_band: 'Actual duration band', route: 'Route', missing_feature: 'Missing feature input' };
function rowSliceValue(row, dimension) {
  if (dimension === 'pickup_hour') return String(row.pickup_hour);
  if (dimension === 'weekday') return String(row.weekday);
  if (dimension === 'duration_band') {
    const value = Number(row.actual_minutes);
    return value < 10 ? 'under_10' : value < 20 ? '10_to_20' : value < 40 ? '20_to_40' : 'over_40';
  }
  if (dimension === 'route') return `${row.pickup_zone} → ${row.dropoff_zone}`;
  if (dimension === 'missing_feature') return row.missing_feature ? 'yes' : 'no';
  return 'all';
}

function updateSliceValues() {
  const dimension = $('#slice-dimension').value;
  const valueSelect = $('#slice-value');
  if (dimension === 'all') { valueSelect.innerHTML = '<option value="all">All values</option>'; valueSelect.disabled = true; return; }
  const values = [...new Set(errorRows.map((row) => rowSliceValue(row, dimension)))].sort();
  valueSelect.innerHTML = '<option value="all">All values</option>' + values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('');
  valueSelect.disabled = false;
}

function renderErrors() {
  const dimension = $('#slice-dimension').value;
  const value = $('#slice-value').value;
  const sortKey = $('#error-sort').value;
  const filtered = errorRows.filter((row) => dimension === 'all' || value === 'all' || rowSliceValue(row, dimension) === value).sort((a, b) => {
    if (sortKey === 'pickup_datetime') return String(a.pickup_datetime).localeCompare(String(b.pickup_datetime));
    return Number(b[sortKey]) - Number(a[sortKey]);
  });
  const meanAbs = filtered.length ? filtered.reduce((sum, row) => sum + Number(row.absolute_error_minutes), 0) / filtered.length : 0;
  $('#error-summary').innerHTML = `<strong>${formatNumber(filtered.length)} holdout rows</strong><span>MAE in current view: ${formatNumber(meanAbs, 3)} minutes · filter: ${escapeHtml(dimension === 'all' ? 'all rows' : `${sliceLabels[dimension]} = ${value === 'all' ? 'all values' : value}`)}</span>`;
  $('#error-table').innerHTML = filtered.length ? `<div class="error-row error-header" role="row"><span>Trip / pickup</span><span>Actual</span><span>Predicted</span><span>Absolute error</span></div>${filtered.map((row) => `<div class="error-row" role="row"><span><strong>${escapeHtml(row.trip_id)}</strong><small>${escapeHtml(row.pickup_datetime)}</small></span><span>${formatNumber(row.actual_minutes, 2)} min</span><span>${formatNumber(row.predicted_minutes, 2)} min</span><span class="${Number(row.absolute_error_minutes) > 5 ? 'error-high' : ''}">${formatNumber(row.absolute_error_minutes, 2)} min</span></div>`).join('')}` : '<p class="empty-state">No holdout errors match this slice.</p>';
}

function localEstimate({ hour, weekday, distance, passengers }) {
  const rush = [7, 8, 9, 16, 17, 18, 19].includes(hour);
  const weekend = weekday >= 5;
  return Math.max(2, 5.5 + (3.9 * distance) + (rush ? 7 : 0) + (weekend ? -1 : 0) + (Math.max(0, passengers - 1) * 0.35));
}

function updateInference() {
  const hour = Number($('#pickup-hour').value);
  const weekday = Number($('#weekday').value);
  const distance = Number($('#distance').value);
  const passengers = Number($('#passengers').value);
  $('#pickup-hour-value').textContent = `${String(hour).padStart(2, '0')}:00`;
  $('#distance-value').textContent = distance.toFixed(1);
  $('#prediction-value').textContent = `${localEstimate({ hour, weekday, distance, passengers }).toFixed(1)} min`;
  $('#prediction-note').textContent = `${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][weekday]} · ${distance.toFixed(1)} mi · ${passengers} passenger${passengers === 1 ? '' : 's'} · toy formula only`;
}

async function loadArtifacts() {
  try {
    const responses = await Promise.all(['metrics.json', 'audit_report.json', 'run_manifest.json', 'prediction_errors.json', 'crispdm_report.md'].map((name) => fetch(`${artifactBase}${name}`)));
    if (responses.some((response) => !response.ok)) throw new Error('Artifact request failed');
    const [metrics, audit, manifest, errors, report] = await Promise.all([responses[0].json(), responses[1].json(), responses[2].json(), responses[3].json(), responses[4].text()]);
    errorRows = errors.rows || [];
    setKpis(metrics); setAudit(audit); setManifest(manifest); renderReport(report);
    $('#slice-dimension').innerHTML = '<option value="all">All holdout rows</option>' + Object.entries(sliceLabels).map(([value, label]) => `<option value="${value}">${label}</option>`).join('');
    updateSliceValues(); renderErrors();
  } catch (error) {
    $('#last-updated').textContent = 'Artifacts unavailable';
    $('#report-panel').innerHTML = '<p>Artifacts could not be loaded. Generate the artifacts and serve the project root as shown in the run guide, then refresh.</p>';
  }
}

$('#inference-form').addEventListener('submit', (event) => { event.preventDefault(); updateInference(); });
['pickup-hour', 'distance', 'weekday', 'passengers'].forEach((id) => { $(`#${id}`).addEventListener('input', updateInference); $(`#${id}`).addEventListener('change', updateInference); });
['audit-severity', 'audit-status'].forEach((id) => $(`#${id}`).addEventListener('change', renderFindings));
$('#audit-search').addEventListener('input', renderFindings);
$('#slice-dimension').addEventListener('change', () => { updateSliceValues(); renderErrors(); });
$('#slice-value').addEventListener('change', renderErrors);
$('#error-sort').addEventListener('change', renderErrors);
document.querySelectorAll('[data-copy]').forEach((button) => button.addEventListener('click', async () => {
  await navigator.clipboard.writeText(button.dataset.copy);
  const original = button.textContent; button.textContent = 'Copied';
  setTimeout(() => { button.textContent = original; }, 1400);
}));
updateInference();
loadArtifacts();
