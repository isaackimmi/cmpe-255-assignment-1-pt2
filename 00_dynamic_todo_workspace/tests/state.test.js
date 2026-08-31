import test from 'node:test';
import assert from 'node:assert/strict';
import { addTask, normalizeTasks, seedTasks, taskCounts, toggleTask, visibleTasks, workflowStages, workflowSummary } from '../src/state.js';

const tasks = [{ id: 1, title: 'Check data', priority: 'high', status: 'todo', meta: 'Data · Today' }, { id: 2, title: 'Review model', priority: 'low', status: 'done', meta: 'Modeling · Yesterday' }];
test('counts tasks by status', () => assert.deepEqual(taskCounts(tasks), { all: 2, todo: 1, done: 1 }));
test('filters by status and case-insensitive search', () => { assert.equal(visibleTasks(tasks, 'todo').length, 1); assert.equal(visibleTasks(tasks, 'all', 'MODEL').at(0).id, 2); });
test('search tolerates missing metadata', () => { assert.equal(visibleTasks([{ id: 1, title: 'Check data', status: 'todo' }], 'all', 'missing').length, 0); });
test('toggleTask changes only the requested task', () => { const updated = toggleTask(tasks, 1); assert.equal(updated[0].status, 'done'); assert.equal(updated[1].status, 'done'); assert.equal(tasks[0].status, 'todo'); });
test('toggleTask canonicalizes string ids and only toggles one matching record', () => {
  const updated = toggleTask([{ id: '1', title: 'First', status: 'todo' }, { id: '1', title: 'Duplicate', status: 'todo' }], 1);
  assert.equal(updated[0].id, 1);
  assert.equal(updated[0].status, 'done');
  assert.equal(updated[1].status, 'todo');
});
test('toggleTask ignores invalid ids', () => {
  const original = [{ id: 1, title: 'First', status: 'todo' }];
  assert.deepEqual(toggleTask(original, true), original);
});
test('addTask prepends a trimmed task with a new id', () => { const updated = addTask(tasks, '  Add feature  ', 'medium'); assert.equal(updated[0].title, 'Add feature'); assert.equal(updated[0].id, 3); assert.equal(updated[0].status, 'todo'); });
test('addTask rejects blank titles and unknown priorities', () => {
  assert.throws(() => addTask(tasks, '   '), /must not be blank/);
  assert.throws(() => addTask(tasks, 'Valid title', 'urgent'), /Unknown task priority/);
});
test('normalizeTasks migrates safe string ids and drops invalid or duplicate records', () => {
  const normalized = normalizeTasks([
    { id: '7', title: '  Keep me  ', priority: 'urgent', status: 'todo' },
    { id: 7, title: 'Duplicate', priority: 'low', status: 'todo', meta: 'ignored' },
    { id: 8, title: 'Bad status', priority: 'low', status: 'blocked', meta: 'discard' },
    { id: 9, title: '', priority: 'low', status: 'done', meta: 'discard' },
  ]);
  assert.deepEqual(normalized, [{ id: 7, title: 'Keep me', priority: 'medium', status: 'todo', meta: '' }]);
});
test('normalizeTasks returns independent seed tasks for non-array storage', () => {
  const normalized = normalizeTasks(null);
  assert.deepEqual(normalized, seedTasks);
  normalized[0].title = 'Changed';
  assert.equal(seedTasks[0].title, 'Validate promotion and holiday flags');
});
test('workflow summary is derived from declared stage statuses', () => {
  assert.deepEqual(workflowSummary(workflowStages), { total: 6, completed: 3, percent: 50, current: 'Modeling' });
});
