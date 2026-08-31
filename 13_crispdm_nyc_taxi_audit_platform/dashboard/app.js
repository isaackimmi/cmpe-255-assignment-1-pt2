const artifactBase = '../artifacts/';

const $ = (selector) => document.querySelector(selector);

function formatPercent(value) {
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function formatNumber(value, digits = 0) {
  return Number(value).toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function setKpis(metrics) {
  $('#kpi-grid').innerHTML = `
    <article class="kpi-card kpi-featured"><span class="kpi-label">Model accuracy</span><strong>${formatPercent(metrics.r2)}</strong><span>R² on chronological holdout</span></article>
    <article class="kpi-card"><span class="kpi-label">Mean absolute error</span><strong>${formatNumber(metrics.mae_minutes, 3)}</strong><span>minutes per trip</span></article>
    <article class="kpi-card"><span class="kpi-label">RMSE</span><strong>${formatNumber(metrics.rmse_minutes, 3)}</strong><span>minutes · holdout</span></article>
    <article class="kpi-card"><span class="kpi-label">Test coverage</span><strong>${formatNumber(metrics.test_rows)}</strong><span>of ${formatNumber(metrics.train_rows)} train rows</span></article>`;
  $('#last-updated').textContent = `${formatNumber(metrics.test_rows)} holdout rows loaded`;
}

function signalFor(value, kind) {
  if (kind === 'good') return '<span class="signal signal-good">Clean</span>';
  return value > 0 ? '<span class="signal signal-watch">Review</span>' : '<span class="signal signal-good">Clean</span>';
}

function setAudit(audit) {
  const missingDistance = audit.null_counts?.distance_miles ?? 0;
  const invalidDuration = audit.invalid_duration_count ?? 0;
  const duplicateIds = audit.duplicate_trip_ids ?? 0;
  const durationOutliers = audit.iqr_outlier_counts?.trip_duration_minutes ?? 0;
  const missingColumns = audit.missing_columns?.length ?? 0;
  const reviewed = missingDistance + invalidDuration + duplicateIds + durationOutliers + missingColumns;
  const rows = [
    ['Missing distances', missingDistance, signalFor(missingDistance)],
    ['Non-positive durations', invalidDuration, signalFor(invalidDuration)],
    ['Duplicate trip IDs', duplicateIds, signalFor(duplicateIds, 'good')],
    ['IQR duration outliers', durationOutliers, signalFor(durationOutliers)],
    ['Missing required columns', missingColumns, signalFor(missingColumns, 'good')],
  ];
  $('#audit-table').innerHTML = `<div class="audit-row audit-header" role="row"><span>Check</span><span>Observed</span><span>Signal</span></div>${rows.map(([label, value, signal]) => `<div class="audit-row" role="row"><span>${label}</span><strong>${formatNumber(value)}</strong>${signal}</div>`).join('')}`;
  $('#audit-summary').innerHTML = `<span class="audit-summary-icon">${reviewed ? '!' : '✓'}</span><div><strong>${reviewed ? `${formatNumber(reviewed)} findings to review` : 'No audit findings'}</strong><span>${formatNumber(audit.rows)} raw rows · before modeling</span></div>`;
}

function inlineMarkdown(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>');
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

function localEstimate({ hour, weekday, distance, passengers }) {
  const rush = [7, 8, 9, 16, 17, 18, 19].includes(hour);
  const weekend = weekday >= 5;
  const trafficAdjustment = rush ? 7 : 0;
  const weekendAdjustment = weekend ? -1 : 0;
  const passengerAdjustment = Math.max(0, passengers - 1) * 0.35;
  return Math.max(2, 5.5 + (3.9 * distance) + trafficAdjustment + weekendAdjustment + passengerAdjustment);
}

function updateInference() {
  const hour = Number($('#pickup-hour').value);
  const weekday = Number($('#weekday').value);
  const distance = Number($('#distance').value);
  const passengers = Number($('#passengers').value);
  $('#pickup-hour-value').textContent = `${String(hour).padStart(2, '0')}:00`;
  $('#distance-value').textContent = distance.toFixed(1);
  const estimate = localEstimate({ hour, weekday, distance, passengers });
  $('#prediction-value').textContent = `${estimate.toFixed(1)} min`;
  $('#prediction-note').textContent = `${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][weekday]} · ${distance.toFixed(1)} mi · ${passengers} passenger${passengers === 1 ? '' : 's'}`;
}

async function loadArtifacts() {
  try {
    const [metricsResponse, auditResponse, reportResponse] = await Promise.all([
      fetch(`${artifactBase}metrics.json`),
      fetch(`${artifactBase}audit_report.json`),
      fetch(`${artifactBase}crispdm_report.md`),
    ]);
    if (!metricsResponse.ok || !auditResponse.ok || !reportResponse.ok) throw new Error('Artifact request failed');
    const [metrics, audit, report] = await Promise.all([metricsResponse.json(), auditResponse.json(), reportResponse.text()]);
    setKpis(metrics); setAudit(audit); renderReport(report);
  } catch (error) {
    $('#last-updated').textContent = 'Run from a local web server';
    $('#report-panel').innerHTML = '<p>Artifacts could not be loaded. Start the local server from the project root as shown in the run guide, then refresh.</p>';
  }
}

$('#inference-form').addEventListener('submit', (event) => { event.preventDefault(); updateInference(); });
['pickup-hour', 'distance', 'weekday', 'passengers'].forEach((id) => { $(`#${id}`).addEventListener('input', updateInference); $(`#${id}`).addEventListener('change', updateInference); });
document.querySelectorAll('[data-copy]').forEach((button) => button.addEventListener('click', async () => {
  await navigator.clipboard.writeText(button.dataset.copy);
  const original = button.textContent; button.textContent = 'Copied';
  setTimeout(() => { button.textContent = original; }, 1400);
}));
updateInference();
loadArtifacts();
