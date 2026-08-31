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
  document.querySelectorAll('.filter').forEach((button) => button.classList.toggle('active', button.dataset.status === activeFilter));
  const visible = visibleTasks(tasks, activeFilter, query);
  $('#taskList').innerHTML = visible.length ? visible.map((task) => `<div class="task ${task.status === 'done' ? 'is-done' : ''}"><button class="check ${task.status === 'done' ? 'checked' : ''}" data-toggle="${task.id}" aria-label="Mark ${esc(task.title)} ${task.status === 'done' ? 'to do' : 'done'}" type="button">${task.status === 'done' ? '✓' : ''}</button><div class="task-copy"><strong>${esc(task.title)}</strong><small>${esc(task.meta)}</small></div><span class="priority ${task.priority}">${task.priority}</span><button class="delete-task" data-delete="${task.id}" aria-label="Delete ${esc(task.title)}" type="button">×</button></div>`).join('') : '<div class="empty-state">No tasks match this view. Add a useful next action.</div>';
  renderStorageStatus();
}

function renderWorkflow() {
  const summary = workflowSummary(workflowStages);
  $('#workflowRing').style.setProperty('--progress', `${summary.percent}%`);
  $('#workflowRing').setAttribute('aria-label', `${summary.percent} percent complete`);
  $('#workflowPercent').textContent = summary.percent;
  $('#workflowCurrent').textContent = `${summary.current} phase`;
  $('#workflowCompleted').textContent = `${summary.completed} of ${summary.total} stages complete`;
  $('#workflowProgress').style.width = `${summary.percent}%`;
  $('#stageList').innerHTML = workflowStages.map((stage, index) => `<div class="stage ${stage.status}"><span>${stage.status === 'complete' ? '✓' : index + 1}</span><div><strong>${esc(stage.name)}</strong><small>${esc(stage.detail)}</small></div></div>`).join('');
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

$('#addTaskButton').setAttribute('aria-expanded', 'false');
$('#addTaskButton').addEventListener('click', () => { $('#taskForm').classList.toggle('hidden'); const open = !$('#taskForm').classList.contains('hidden'); $('#addTaskButton').setAttribute('aria-expanded', String(open)); if (open) $('#taskTitle').focus(); });
$('#taskForm').addEventListener('submit', (event) => { event.preventDefault(); const title = $('#taskTitle').value.trim(); if (!title) return; try { tasks = addTask(tasks, title, $('#taskPriority').value); } catch { return; } save(); renderTasks(); event.target.reset(); $('#taskForm').classList.add('hidden'); logActivity('Task added', title, 'info'); });
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
$('#runAgentButton').addEventListener('click', (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.innerHTML = '<span>◌</span> Simulating…';
  logActivity('Demo check started', 'Reviewing the local task queue; no dataset or model is connected.', 'info');
  setTimeout(() => {
    button.disabled = false;
    button.innerHTML = '<span>✦</span> Simulate agent check';
    logActivity('Demo check completed', 'No queue blockers found. Forecasting, leakage, and model evaluation were not run.', 'good');
  }, 700);
});
$('#clearActivity').addEventListener('click', () => { activities = []; saveActivities(); renderActivity(); renderStorageStatus(); });
document.addEventListener('keydown', (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#searchInput').focus(); } });
document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !$('#taskForm').classList.contains('hidden')) { $('#taskForm').classList.add('hidden'); $('#addTaskButton').setAttribute('aria-expanded', 'false'); $('#addTaskButton').focus(); } });
renderTasks();
renderWorkflow();
renderActivity();
