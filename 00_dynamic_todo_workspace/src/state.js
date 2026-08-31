export const TASK_STATUSES = Object.freeze(['todo', 'done']);
export const TASK_PRIORITIES = Object.freeze(['high', 'medium', 'low']);

export const seedTasks = [
  { id: 1, title: 'Validate promotion and holiday flags', priority: 'high', status: 'todo', meta: 'Data prep · Due today' },
  { id: 2, title: 'Compare seasonal naive baseline', priority: 'medium', status: 'todo', meta: 'Modeling · Due tomorrow' },
  { id: 3, title: 'Review outlier stores with agent', priority: 'low', status: 'todo', meta: 'Data understanding · Due Sep 10' },
  { id: 4, title: 'Write stakeholder readout', priority: 'medium', status: 'done', meta: 'Business understanding · Completed yesterday' },
];

// This is the plan shown by the demo. It is deliberately separate from task
// state so the UI cannot display a completion count that disagrees with it.
export const workflowStages = Object.freeze([
  { name: 'Business understanding', status: 'complete', detail: 'Goal and constraints captured' },
  { name: 'Data understanding', status: 'complete', detail: 'Schema and quality review planned' },
  { name: 'Data preparation', status: 'complete', detail: 'Feature plan documented' },
  { name: 'Modeling', status: 'current', detail: 'Baseline comparison planned' },
  { name: 'Evaluation', status: 'planned', detail: 'Waiting on model artifacts' },
  { name: 'Deployment', status: 'planned', detail: 'Planned after sign-off' },
]);

const validStatuses = new Set(TASK_STATUSES);
const validPriorities = new Set(TASK_PRIORITIES);

export function cloneSeedTasks() {
  return seedTasks.map((task) => ({ ...task }));
}

function canonicalTaskId(id) {
  if (typeof id === 'string' && !/^\d+$/.test(id.trim())) return null;
  if (typeof id !== 'number' && typeof id !== 'string') return null;
  const numericId = Number(id);
  return Number.isSafeInteger(numericId) && numericId > 0 ? numericId : null;
}

export function normalizeTask(task) {
  if (!task || typeof task !== 'object') return null;
  const id = canonicalTaskId(task.id);
  const title = typeof task.title === 'string' ? task.title.trim() : '';
  const status = task.status;
  const priority = task.priority;
  if (id === null || !title || !validStatuses.has(status)) return null;
  return {
    id,
    title,
    priority: validPriorities.has(priority) ? priority : 'medium',
    status,
    meta: typeof task.meta === 'string' ? task.meta : '',
  };
}

/** Normalize local-storage data and drop malformed or duplicate records. */
export function normalizeTasks(rawTasks) {
  if (!Array.isArray(rawTasks)) return cloneSeedTasks();
  const seenIds = new Set();
  return rawTasks.reduce((normalized, task) => {
    const cleanTask = normalizeTask(task);
    if (!cleanTask || seenIds.has(cleanTask.id)) return normalized;
    seenIds.add(cleanTask.id);
    normalized.push(cleanTask);
    return normalized;
  }, []);
}

export function visibleTasks(tasks, filter = 'all', query = '') {
  const normalized = String(query ?? '').trim().toLowerCase();
  return tasks.filter((task) => {
    const title = String(task?.title ?? '').toLowerCase();
    const meta = String(task?.meta ?? '').toLowerCase();
    return (filter === 'all' || task?.status === filter) && (!normalized || title.includes(normalized) || meta.includes(normalized));
  });
}

export function taskCounts(tasks) {
  return { all: tasks.length, todo: tasks.filter((task) => task.status === 'todo').length, done: tasks.filter((task) => task.status === 'done').length };
}

export function toggleTask(tasks, id) {
  const targetId = canonicalTaskId(id);
  if (targetId === null) return tasks.slice();
  let toggled = false;
  return tasks.map((task) => {
    if (toggled || canonicalTaskId(task.id) !== targetId) return task;
    toggled = true;
    return { ...task, id: targetId, status: task.status === 'done' ? 'todo' : 'done' };
  });
}

export function addTask(tasks, title, priority = 'medium') {
  if (typeof title !== 'string' || !title.trim()) throw new TypeError('Task title must not be blank');
  if (!validPriorities.has(priority)) throw new RangeError(`Unknown task priority: ${priority}`);
  const nextId = tasks.reduce((max, task) => Math.max(max, canonicalTaskId(task.id) ?? 0), 0) + 1;
  return [{ id: nextId, title: title.trim(), priority, status: 'todo', meta: 'Workspace · Just added' }, ...tasks];
}

export function workflowSummary(stages = workflowStages) {
  const total = stages.length;
  const completed = stages.filter((stage) => stage.status === 'complete').length;
  const current = stages.find((stage) => stage.status === 'current');
  return {
    total,
    completed,
    percent: total ? Math.round((completed / total) * 100) : 0,
    current: current?.name ?? 'Complete',
  };
}
