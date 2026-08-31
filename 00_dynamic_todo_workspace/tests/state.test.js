import test from 'node:test';
import assert from 'node:assert/strict';
import { addTask, taskCounts, toggleTask, visibleTasks } from '../src/state.js';

const tasks = [{ id: 1, title: 'Check data', priority: 'high', status: 'todo', meta: 'Data · Today' }, { id: 2, title: 'Review model', priority: 'low', status: 'done', meta: 'Modeling · Yesterday' }];
test('counts tasks by status', () => assert.deepEqual(taskCounts(tasks), { all: 2, todo: 1, done: 1 }));
test('filters by status and case-insensitive search', () => { assert.equal(visibleTasks(tasks, 'todo').length, 1); assert.equal(visibleTasks(tasks, 'all', 'MODEL').at(0).id, 2); });
test('toggleTask changes only the requested task', () => { const updated = toggleTask(tasks, 1); assert.equal(updated[0].status, 'done'); assert.equal(updated[1].status, 'done'); assert.equal(tasks[0].status, 'todo'); });
test('addTask prepends a trimmed task with a new id', () => { const updated = addTask(tasks, '  Add feature  ', 'medium'); assert.equal(updated[0].title, 'Add feature'); assert.equal(updated[0].id, 3); assert.equal(updated[0].status, 'todo'); });
