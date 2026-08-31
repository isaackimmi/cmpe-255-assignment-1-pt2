import {
  cloneSeedTasks,
  normalizeTasks,
  visibleTasks,
  taskCounts,
  toggleTask,
  addTask,
  workflowStages,
  workflowSummary,
} from './state.js';

const storageKey = 'fieldnote-project-00-tasks';
const activityStorageKey = 'fieldnote-project-00-activities';
let storageAvailable = false;
let tasksPersisted = false;
let activitiesPersisted = false;
let tasks = loadTasks();
let activeFilter = 'all';
let query = '';
let selectedStageIndex = workflowStages.findIndex((stage) => stage.status === 'current');

const demoActivities = [
  { timestamp: null, title: 'Demo context loaded', detail: 'Seeded examples are illustrative; no dataset or model is connected.', tone: 'info' },
  { timestamp: null, title: 'Demo quality note', detail: 'Data quality is not measured in this local planning workspace.', tone: 'warn' },
  { timestamp: null, title: 'Baseline task suggested', detail: 'Compare a seasonal-naive baseline when the forecasting pipeline is implemented.', tone: 'info' },
];
let activities = loadActivities();

const $ = (selector) => document.querySelector(selector);

function loadTasks() {
  try {
    const saved = window.localStorage.getItem(storageKey);
    storageAvailable = true;
    tasksPersisted = true;
    if (saved === null) return cloneSeedTasks();
    const normalized = normalizeTasks(JSON.parse(saved));
    // Write the clean representation back so the migration is one-time.
    if (JSON.stringify(normalized) !== saved) {
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(normalized));
      } catch {
        storageAvailable = false;
        tasksPersisted = false;
      }
    }
    return normalized;
  } catch {
    storageAvailable = false;
    tasksPersisted = false;
    return cloneSeedTasks();
  }
}

function loadActivities() {
  if (!storageAvailable) return demoActivities.map((activity) => ({ ...activity }));
  try {
    const saved = window.localStorage.getItem(activityStorageKey);
    activitiesPersisted = true;
    if (saved === null) return demoActivities.map((activity) => ({ ...activity }));
    const parsed = JSON.parse(saved);
    if (!Array.isArray(parsed)) return demoActivities.map((activity) => ({ ...activity }));
    const valid = parsed.filter((activity) => activity && typeof activity.title === 'string' && typeof activity.detail === 'string' && typeof activity.tone === 'string')
      .map((activity) => ({ timestamp: typeof activity.timestamp === 'string' ? activity.timestamp : null, title: activity.title, detail: activity.detail, tone: activity.tone }));
    return valid.length ? valid : demoActivities.map((activity) => ({ ...activity }));
  } catch {
    activitiesPersisted = false;
    return demoActivities.map((activity) => ({ ...activity }));
  }
}

function save() {
  try {
    window.localStorage.setItem(storageKey, JSON.stringify(tasks));
    storageAvailable = true;
    tasksPersisted = true;
    return true;
  } catch {
    storageAvailable = false;
    tasksPersisted = false;
    return false;
  }
}

function saveActivities() {
  try {
    window.localStorage.setItem(activityStorageKey, JSON.stringify(activities));
    storageAvailable = true;
    activitiesPersisted = true;
    return true;
  } catch {
    storageAvailable = false;
    activitiesPersisted = false;
    return false;
  }
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
}

function renderStorageStatus() {
  const status = $('#storageStatus');
  if (!status) return;
  status.textContent = storageAvailable && tasksPersisted && activitiesPersisted
    ? 'Local workspace · saved locally when changed'
    : 'Local workspace · browser storage unavailable; session-only changes';
}

function renderTasks() {
  const counts = taskCounts(tasks);
  $('#allCount').textContent = counts.all;
  $('#todoCount').textContent = counts.todo;
  $('#doneCount').textContent = counts.done;
  $('#completedStat').textContent = `${counts.done} / ${counts.all}`;
  document.querySelectorAll('.filter').forEach((button) => {
    const selected = button.dataset.status === activeFilter;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  const visible = visibleTasks(tasks, activeFilter, query);
  $('#taskList').innerHTML = visible.length ? visible.map((task) => `<div class="task ${task.status === 'done' ? 'is-done' : ''}"><button class="check ${task.status === 'done' ? 'checked' : ''}" data-toggle="${task.id}" aria-label="Mark ${esc(task.title)} ${task.status === 'done' ? 'to do' : 'done'}" type="button">${task.status === 'done' ? '✓' : ''}</button><div class="task-copy"><strong>${esc(task.title)}</strong><small>${esc(task.meta)}</small></div><span class="priority ${task.priority}">${task.priority}</span><button class="delete-task" data-delete="${task.id}" aria-label="Delete ${esc(task.title)}" type="button">×</button></div>`).join('') : '<div class="empty-state">No tasks match this view. Add a useful next action.</div>';
  renderStorageStatus();
}

function renderWorkflow() {
  const summary = workflowSummary(workflowStages);
  $('#workflowRing').style.setProperty('--progress', `${summary.percent}%`);
  $('#workflowRing').setAttribute('aria-label', `Example plan ${summary.percent} percent drafted`);
  $('#workflowPercent').textContent = summary.percent;
  $('#workflowCurrent').textContent = `${summary.current} phase`;
  $('#workflowCompleted').textContent = `${summary.completed} of ${summary.total} stages drafted`;
  $('#workflowProgress').style.width = `${summary.percent}%`;
  $('#stageList').innerHTML = workflowStages.map((stage, index) => `<button class="stage ${stage.status}" data-stage-index="${index}" aria-pressed="${index === selectedStageIndex}" type="button"><span>${stage.status === 'complete' ? '✓' : index + 1}</span><div><strong>${esc(stage.name)}</strong><small>${esc(stage.detail)}</small></div></button>`).join('');
  const selectedStage = workflowStages[selectedStageIndex] ?? workflowStages[0];
  $('#stageDetail').innerHTML = selectedStage
    ? `<strong>${esc(selectedStage.name)} evidence status</strong><p>${esc(selectedStage.detail)}. This example plan has no connected run artifact.</p>`
    : '';
}

function formatActivityTime(timestamp) {
  if (!timestamp) return 'Demo';
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? 'Unknown' : new Intl.DateTimeFormat([], { hour: '2-digit', minute: '2-digit' }).format(date);
}

function renderActivity() {
  $('#activityList').innerHTML = activities.length ? activities.slice(0, 4).map((activity) => `<div class="activity"><span class="activity-dot ${esc(activity.tone)}"></span><div><div class="activity-title"><strong>${esc(activity.title)}</strong><time>${formatActivityTime(activity.timestamp)}</time></div><p>${esc(activity.detail)}</p></div></div>`).join('') : '<div class="empty-state">Activity cleared.</div>';
}

function logActivity(title, detail, tone = 'info') {
  activities.unshift({ timestamp: new Date().toISOString(), title, detail, tone });
  activities = activities.slice(0, 20);
  saveActivities();
  renderActivity();
  renderStorageStatus();
}

function setTaskFormOpen(open, focusTitle = false) {
  $('#taskForm').classList.toggle('hidden', !open);
  $('#addTaskButton').setAttribute('aria-expanded', String(open));
  if (open && focusTitle) $('#taskTitle').focus();
}

const dialogCopy = {
  'agent-runs': {
    title: 'Agent runs',
    body: '<p>No connected agent runs are available.</p><p>The button on this page only records a simulated queue check in the local activity log. It does not inspect data, train a model, or produce evaluation metrics.</p>',
  },
  datasets: {
    title: 'Dataset readiness',
    body: '<p><strong>retail_orders.parquet</strong> is a planned input, not a connected file.</p><div class="readiness-list"><div><span>Dataset connection</span><strong>Not connected</strong></div><div><span>Schema profile</span><strong>Planned</strong></div><div><span>Time coverage</span><strong>Not measured</strong></div><div><span>Leakage checks</span><strong>Not run</strong></div></div><p class="dialog-note">Connect a versioned dataset and profile artifact before treating any quality or forecast result as measured.</p>',
  },
  notifications: {
    title: 'Notifications',
    body: '<p>No new notifications. Local task changes appear in the activity log.</p>',
  },
  help: {
    title: 'Using this workspace',
    body: '<p>Add, filter, search, complete, or remove tasks in the work queue. Select a workflow stage to inspect the evidence expected next.</p><p>This is a local-first CRISP-DM planning demo. Forecasting, data profiling, leakage checks, and model evaluation are not connected.</p>',
  },
};

function showDialog(kind, customTitle = null, customBody = null) {
  const copy = dialogCopy[kind];
  if (!copy) return;
  const dialog = $('#infoDialog');
  $('#infoDialogTitle').textContent = customTitle ?? copy.title;
  $('#infoDialogBody').innerHTML = customBody ?? copy.body;
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else dialog.setAttribute('open', '');
}

function closeDialog() {
  const dialog = $('#infoDialog');
  if (typeof dialog.close === 'function') dialog.close();
  else dialog.removeAttribute('open');
}

$('#addTaskButton').addEventListener('click', () => setTaskFormOpen($('#taskForm').classList.contains('hidden'), true));
$('#taskForm').addEventListener('submit', (event) => { event.preventDefault(); const title = $('#taskTitle').value.trim(); if (!title) return; try { tasks = addTask(tasks, title, $('#taskPriority').value); } catch { return; } save(); renderTasks(); event.target.reset(); setTaskFormOpen(false); logActivity('Task added', title, 'info'); $('#addTaskButton').focus(); });
document.querySelectorAll('.filter').forEach((button) => button.addEventListener('click', () => { activeFilter = button.dataset.status; renderTasks(); }));
$('#searchInput').addEventListener('input', (event) => { query = event.target.value; renderTasks(); });
$('#taskList').addEventListener('click', (event) => {
  const toggle = event.target.closest('[data-toggle]');
  const remove = event.target.closest('[data-delete]');
  const taskId = Number(toggle?.dataset.toggle ?? remove?.dataset.delete);
  if (!Number.isSafeInteger(taskId)) return;
  const task = tasks.find((item) => item.id === taskId);
  if (!task) return;
  if (toggle) {
    tasks = toggleTask(tasks, taskId);
    save();
    renderTasks();
    logActivity(task.status === 'done' ? 'Task reopened' : 'Task completed', task.title, 'good');
  } else if (remove) {
    tasks = tasks.filter((item) => item.id !== taskId);
    save();
    renderTasks();
    logActivity('Task removed', task.title, 'warn');
  }
});
document.querySelectorAll('[data-dialog]').forEach((control) => control.addEventListener('click', () => {
  if (control.classList.contains('nav-item')) document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item === control));
  showDialog(control.dataset.dialog);
}));
document.querySelectorAll('.nav-item[data-target]').forEach((control) => control.addEventListener('click', () => {
  document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item === control));
  document.getElementById(control.dataset.target)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}));
$('#stageList').addEventListener('click', (event) => {
  const stage = event.target.closest('[data-stage-index]');
  if (!stage) return;
  selectedStageIndex = Number(stage.dataset.stageIndex);
  renderWorkflow();
});
$('#runAgentButton').addEventListener('click', (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  button.innerHTML = '<span>◌</span> Simulating…';
  logActivity('Demo check started', 'Reviewing the local task queue; no dataset or model is connected.', 'info');
  setTimeout(() => {
    button.disabled = false;
    button.setAttribute('aria-busy', 'false');
    button.innerHTML = '<span>✦</span> Simulate agent check';
    logActivity('Demo check completed', 'No queue blockers found. Forecasting, leakage, and model evaluation were not run.', 'good');
  }, 700);
});
$('#closeDialog').addEventListener('click', closeDialog);
$('#infoDialog').addEventListener('click', (event) => { if (event.target === event.currentTarget) closeDialog(); });
$('#clearActivity').addEventListener('click', () => { activities = []; saveActivities(); renderActivity(); renderStorageStatus(); });
document.addEventListener('keydown', (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#searchInput').focus(); } });
document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !$('#taskForm').classList.contains('hidden')) { setTaskFormOpen(false); $('#addTaskButton').focus(); } });
renderTasks();
renderWorkflow();
renderActivity();
