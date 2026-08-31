export const seedTasks = [
  { id: 1, title: 'Validate promotion and holiday flags', priority: 'high', status: 'todo', meta: 'Data prep · Due today' },
  { id: 2, title: 'Compare seasonal naive baseline', priority: 'medium', status: 'todo', meta: 'Modeling · Due tomorrow' },
  { id: 3, title: 'Review outlier stores with agent', priority: 'low', status: 'todo', meta: 'Data understanding · Due Sep 10' },
  { id: 4, title: 'Write stakeholder readout', priority: 'medium', status: 'done', meta: 'Business understanding · Completed yesterday' },
];

export function visibleTasks(tasks, filter = 'all', query = '') {
  const normalized = query.trim().toLowerCase();
  return tasks.filter((task) => (filter === 'all' || task.status === filter) && (!normalized || task.title.toLowerCase().includes(normalized) || task.meta.toLowerCase().includes(normalized)));
}

export function taskCounts(tasks) {
  return { all: tasks.length, todo: tasks.filter((t) => t.status === 'todo').length, done: tasks.filter((t) => t.status === 'done').length };
}

export function toggleTask(tasks, id) {
  return tasks.map((task) => task.id === id ? { ...task, status: task.status === 'done' ? 'todo' : 'done' } : task);
}

export function addTask(tasks, title, priority = 'medium') {
  const nextId = tasks.reduce((max, task) => Math.max(max, Number(task.id) || 0), 0) + 1;
  return [{ id: nextId, title: title.trim(), priority, status: 'todo', meta: 'Agent workspace · Just added' }, ...tasks];
}
