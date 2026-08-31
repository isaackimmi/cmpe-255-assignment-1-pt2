import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const read = (name) => readFile(join(root, name), 'utf8');

test('HTML keeps the local planning boundary visible', async () => {
  const html = await read('index.html');
  assert.match(html, /Not connected/);
  assert.match(html, /Not measured/);
  assert.match(html, /Example workflow/);
  assert.match(html, /no dataset or model is connected yet/i);
  assert.doesNotMatch(html, /2\.4M rows|38 columns|94%|87%|4\.5h|68%/);
});

test('interactive controls expose their state and honest status views', async () => {
  const [html, app] = await Promise.all([read('index.html'), read('src/app.js')]);
  assert.match(html, /aria-controls="taskForm" aria-expanded="false"/);
  assert.match(html, /aria-pressed="true"/);
  assert.match(html, /Search tasks/);
  assert.match(html, /id="dataQualityButton" data-dialog="datasets"/);
  assert.match(app, /button\.setAttribute\('aria-pressed', String\(selected\)\)/);
  assert.match(app, /setTaskFormOpen\(false\)/);
  assert.match(app, /No connected agent runs are available/);
  assert.match(app, /Leakage checks.*Not run/);
});
