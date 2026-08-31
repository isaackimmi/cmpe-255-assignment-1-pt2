import { seedTasks, visibleTasks, taskCounts, toggleTask, addTask } from './state.js';

const storageKey = 'fieldnote-project-00-tasks';
let tasks = loadTasks();
let activeFilter = 'all';
let query = '';
let activities = [
  ['09:42', 'Agent found a stable weekly cadence', 'Seasonality signal is strong in 84% of stores.', 'good'],
  ['09:36', 'Data quality check completed', '12 missing promotion values were flagged for review.', 'warn'],
  ['09:18', 'Feature suggestion added', 'Try lag_4 and rolling_mean_8 for the next baseline.', 'info'],
];

const $ = (selector) => document.querySelector(selector);
function loadTasks() { try { const saved = JSON.parse(localStorage.getItem(storageKey)); return Array.isArray(saved) ? saved : seedTasks.map((task) => ({ ...task })); } catch { return seedTasks.map((task) => ({ ...task })); } }
function save() { try { localStorage.setItem(storageKey, JSON.stringify(tasks)); } catch { /* local-only file mode */ } }
function esc(value) { return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char])); }

function renderTasks() {
  const counts = taskCounts(tasks);
  $('#allCount').textContent = counts.all; $('#todoCount').textContent = counts.todo; $('#doneCount').textContent = counts.done;
  $('#completedStat').textContent = `${counts.done} / ${counts.all}`;
  document.querySelectorAll('.filter').forEach((button) => button.classList.toggle('active', button.dataset.status === activeFilter));
  const visible = visibleTasks(tasks, activeFilter, query);
  $('#taskList').innerHTML = visible.length ? visible.map((task) => `<div class="task ${task.status === 'done' ? 'is-done' : ''}"><button class="check ${task.status === 'done' ? 'checked' : ''}" data-toggle="${task.id}" aria-label="Mark ${esc(task.title)} ${task.status === 'done' ? 'to do' : 'done'}" type="button">${task.status === 'done' ? '✓' : ''}</button><div class="task-copy"><strong>${esc(task.title)}</strong><small>${esc(task.meta)}</small></div><span class="priority ${task.priority}">${task.priority}</span><button class="delete-task" data-delete="${task.id}" aria-label="Delete ${esc(task.title)}" type="button">×</button></div>`).join('') : '<div class="empty-state">No tasks match this view. Add a useful next action.</div>';
}
function renderActivity() { $('#activityList').innerHTML = activities.length ? activities.map(([time, title, detail, tone]) => `<div class="activity"><span class="activity-dot ${tone}"></span><div><div class="activity-title"><strong>${esc(title)}</strong><time>${time}</time></div><p>${esc(detail)}</p></div></div>`).join('') : '<div class="empty-state">Activity cleared.</div>'; }
function logActivity(title, detail, tone = 'info') { activities.unshift([new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), title, detail, tone]); activities = activities.slice(0, 4); renderActivity(); }

$('#addTaskButton').setAttribute('aria-expanded', 'false');
$('#addTaskButton').addEventListener('click', () => { $('#taskForm').classList.toggle('hidden'); const open = !$('#taskForm').classList.contains('hidden'); $('#addTaskButton').setAttribute('aria-expanded', String(open)); if (open) $('#taskTitle').focus(); });
$('#taskForm').addEventListener('submit', (event) => { event.preventDefault(); const title = $('#taskTitle').value.trim(); if (!title) return; tasks = addTask(tasks, title, $('#taskPriority').value); save(); renderTasks(); event.target.reset(); $('#taskForm').classList.add('hidden'); logActivity('New task added', title, 'info'); });
document.querySelectorAll('.filter').forEach((button) => button.addEventListener('click', () => { activeFilter = button.dataset.status; renderTasks(); }));
$('#searchInput').addEventListener('input', (event) => { query = event.target.value; renderTasks(); });
$('#taskList').addEventListener('click', (event) => { const toggle = event.target.closest('[data-toggle]'); const remove = event.target.closest('[data-delete]'); if (toggle) { const task = tasks.find((item) => item.id === Number(toggle.dataset.toggle)); tasks = toggleTask(tasks, Number(toggle.dataset.toggle)); save(); renderTasks(); logActivity(task?.status === 'done' ? 'Task reopened' : 'Task completed', task?.title || 'Queue updated', 'good'); } if (remove) { const task = tasks.find((item) => item.id === Number(remove.dataset.delete)); tasks = tasks.filter((item) => item.id !== Number(remove.dataset.delete)); save(); renderTasks(); logActivity('Task removed', task?.title || 'Queue updated', 'warn'); } });
$('#runAgentButton').addEventListener('click', (event) => { const button = event.currentTarget; button.disabled = true; button.innerHTML = '<span>◌</span> Checking…'; logActivity('Agent check started', 'Scanning queue and current dataset context.', 'info'); setTimeout(() => { button.disabled = false; button.innerHTML = '<span>✦</span> Run agent check'; logActivity('Agent check completed', 'No blocking issues found in the current queue.', 'good'); }, 700); });
$('#clearActivity').addEventListener('click', () => { activities = []; renderActivity(); });
document.addEventListener('keydown', (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#searchInput').focus(); } });
document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !$('#taskForm').classList.contains('hidden')) { $('#taskForm').classList.add('hidden'); $('#addTaskButton').setAttribute('aria-expanded', 'false'); $('#addTaskButton').focus(); } });
renderTasks(); renderActivity();
