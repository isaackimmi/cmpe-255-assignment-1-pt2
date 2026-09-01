import "./style.css";

const app = document.querySelector("#app");
const state = { metrics: null, behavior: null };

app.innerHTML = `
  <header class="topbar"><a class="brand" href="#top"><span class="mark">N</span>nano<span class="orange">/llm</span></a><nav><a href="#evidence">Evidence</a><a href="#playground">Replay</a><a href="#method">Method</a></nav><span id="connection" class="status">● connecting</span></header><div id="api-error" class="api-error" role="alert" aria-live="assertive" hidden></div>
  <main id="top">
    <section class="hero"><div><p class="kicker">PROJECT 02 · CAUSAL LANGUAGE MODELING</p><h1>Small model.<br><em>Clear evidence.</em></h1><p class="lede">An interactive evidence studio for a character-level language model. Follow the data split, inspect probabilities, and replay generation through a real API.</p><div class="actions"><a class="button" href="#playground">Open replay ↓</a><a href="#method">How it works ↗</a></div></div><div class="hero-core"><span>next</span><strong>char</strong><small>context → prediction</small></div></section>
    <section class="metric-grid" id="evidence"><article><span>TEST PERPLEXITY</span><strong id="perplexity">—</strong><small>conditional character stream</small></article><article><span>BACKEND</span><strong id="backend">—</strong><small id="backend-note">artifact</small></article><article><span>TEST LOSS</span><strong id="loss">—</strong><small>nats per character</small></article><article><span>TEST TARGETS</span><strong id="targets">—</strong><small>chronological holdout</small></article></section>
    <section class="evidence-grid"><article class="panel"><p class="kicker">DATA CONTRACT</p><h2>One corpus, three honest splits.</h2><div class="split-bar"><i id="train-bar"></i><i id="validation-bar"></i><i id="test-bar"></i></div><div class="split-labels"><span>TRAIN <b id="train-chars">—</b></span><span>VALIDATION <b id="validation-chars">—</b></span><span>TEST <b id="test-chars">—</b></span></div><p class="annotation">The vocabulary is fitted on training characters only. Unseen validation/test characters map to <code>&lt;UNK&gt;</code>; the test suffix is evaluated once after model selection.</p></article><article class="panel"><p class="kicker">RUN MANIFEST</p><h2>Reproducible by design.</h2><dl><dt>Seed</dt><dd id="seed">—</dd><dt>Context order</dt><dd id="order">—</dd><dt>Vocabulary</dt><dd id="vocab">—</dd><dt>Device</dt><dd id="device">—</dd><dt>Corpus hash</dt><dd id="hash">—</dd></dl></article></section>
    <section class="playground" id="playground"><div class="section-head"><div><p class="kicker">LIVE API PLAYGROUND</p><h2>Watch the next character happen.</h2><p>The browser calls FastAPI, which loads the local model adapter and returns a bounded, auditable generation trace.</p></div><span class="api-badge">POST /api/generate</span></div><div class="play-grid"><article class="panel"><div class="chat-head"><strong>Generation request</strong><span id="request-state">ready</span></div><label for="prompt">Prompt</label><textarea id="prompt" rows="3">user: explain a transformer
assistant:</textarea><div class="form-row"><label>New characters <input id="max-tokens" type="number" min="1" max="40" value="16"></label><label>Temperature <input id="temperature" type="number" min="0" max="2" step="0.1" value="0"></label><button id="generate" class="button" type="button">Generate ↗</button></div><div class="response"><span>MODEL RESPONSE</span><pre id="generated">Submit a prompt to inspect the model response.</pre></div></article><article class="panel"><div class="chat-head"><strong>Behavior inspector</strong><span class="pill" id="trace-badge">WAITING</span></div><div class="context-card"><span>LAST CONTEXT WINDOW</span><code id="context">—</code><small id="context-note">order —</small></div><div class="subhead"><span>NEXT-CHARACTER PROBABILITIES</span><small id="candidate-count">—</small></div><div id="probability-list" class="prob-list"><p class="empty">Generate a response to see normalized probabilities.</p></div><div class="subhead trace-heading"><span>GENERATION TRACE</span><small id="trace-count">0 steps</small></div><div id="trace-list" class="trace-list"><p class="empty">Selected characters will appear here with their context.</p></div></article></div></section>
    <section class="method" id="method"><p class="kicker">CRISP-DM · MODEL CARD</p><h2>Transparent mechanics beat impressive claims.</h2><div class="method-grid"><article><b>01 · Prepare</b><p>Preserve character order and split 80/10/10 chronologically to prevent future-character leakage.</p></article><article><b>02 · Model</b><p>The default is a smoothed character n-gram. The optional Torch path adds a causal Transformer.</p></article><article><b>03 · Evaluate</b><p>Validation informs selection; the untouched test suffix reports loss, perplexity, and OOV rate.</p></article></div></section>
  </main><footer>Teaching miniature · local artifacts · no pretrained weights <a href="https://github.com/isaackimmi/cmpe-255-assignment-1-pt2/tree/assignment-1-part-2-reproduction/02_nano_llm_transformer" target="_blank" rel="noreferrer">Read the README ↗</a></footer>`;

const $ = (id) => document.querySelector(id);
$("#max-tokens").max = "80";
const set = (id, value) => { const node = $(id); if (node) node.textContent = value; };
const token = (value) => value === "\n" ? "↵" : value === " " ? "·" : value || "∅";
const pct = (value) => `${(Number(value) * 100).toFixed(1)}%`;

function renderMetrics(metrics) {
  state.metrics = metrics;
  const split = metrics.split || {};
  set("#perplexity", metrics.test?.perplexity ?? metrics.perplexity ?? "—");
  set("#backend", metrics.backend === "stdlib_char_ngram" ? "CHAR N-GRAM" : String(metrics.backend || "—").toUpperCase());
  set("#backend-note", `${metrics.device || "cpu"} · seed ${metrics.seed ?? "—"}`);
  set("#loss", metrics.test?.loss ?? metrics.loss ?? "—");
  set("#targets", metrics.test?.target_chars ?? metrics.test_chars ?? "—");
  set("#train-chars", split.train_chars ?? "—"); set("#validation-chars", split.validation_chars ?? "—"); set("#test-chars", split.test_chars ?? "—");
  set("#seed", metrics.seed ?? "—"); set("#order", metrics.behavior?.order ?? metrics.config?.order ?? "—"); set("#vocab", metrics.vocab_size ?? metrics.vocabulary?.length ?? "—"); set("#device", metrics.device ?? "—"); set("#hash", `${String(metrics.corpus_sha256 || "—").slice(0, 12)}…`);
  const total = Number(split.train_chars || 0) + Number(split.validation_chars || 0) + Number(split.test_chars || 0);
  if (total) ["train", "validation", "test"].forEach((key) => { $(`#${key}-bar`).style.width = `${Number(split[`${key}_chars`] || 0) / total * 100}%`; });
}

function renderReplay(replay) {
  const first = replay.trace?.[0];
  set("#generated", replay.generated || "(no new characters)"); set("#trace-badge", replay.deterministic ? "DETERMINISTIC" : "REPLAY"); set("#context", first?.context || "∅"); set("#context-note", `order ${replay.context_order ?? "—"}`); set("#trace-count", `${replay.trace?.length || 0} steps`); set("#candidate-count", `${first?.candidates?.length || 0} candidates`);
  const probabilityList = $("#probability-list"); probabilityList.replaceChildren();
  (first?.candidates || []).forEach((item) => { const row = document.createElement("div"); row.className = "prob-row"; const label = document.createElement("b"); label.textContent = token(item.token); const track = document.createElement("i"); const fill = document.createElement("span"); fill.style.width = `${Math.max(2, Number(item.probability) * 100)}%`; track.append(fill); const value = document.createElement("strong"); value.textContent = pct(item.probability); row.append(label, track, value); probabilityList.append(row); });
  if (!first?.candidates?.length) { const empty = document.createElement("p"); empty.className = "empty"; empty.textContent = "No candidates returned."; probabilityList.append(empty); }
  const traceList = $("#trace-list"); traceList.replaceChildren();
  (replay.trace || []).forEach((step) => { const row = document.createElement("div"); row.className = "trace-row"; const number = document.createElement("b"); number.textContent = String(step.step).padStart(2, "0"); const context = document.createElement("code"); context.textContent = step.context || "∅"; const selected = document.createElement("strong"); selected.textContent = token(step.selected); const candidates = document.createElement("span"); candidates.textContent = (step.candidates || []).slice(0, 3).map((item) => `${token(item.token)} ${pct(item.probability)}`).join(" · "); row.append(number, context, selected, candidates); traceList.append(row); });
  if (!replay.trace?.length) { const empty = document.createElement("p"); empty.className = "empty"; empty.textContent = "No trace returned."; traceList.append(empty); }
}

function showError(message) { const node = $("#api-error"); node.textContent = `API error: ${message}`; node.hidden = false; }
function errorMessage(response, fallback) { return response.json().then((payload) => payload?.error?.message || payload?.detail || fallback).catch(() => fallback); }

async function load() {
  try {
    const [metricsResponse, behaviorResponse] = await Promise.all([fetch("/api/metrics"), fetch("/api/behavior")]);
    if (!metricsResponse.ok || !behaviorResponse.ok) throw new Error("API unavailable");
    state.behavior = await behaviorResponse.json();
    renderMetrics(await metricsResponse.json());
    set("#connection", "● API connected"); $("#connection").classList.add("connected");
  }
  catch (_) { set("#connection", "● API unavailable"); $("#connection").classList.add("error"); showError("The FastAPI service is unavailable or its artifact failed validation."); }
}

$("#generate").addEventListener("click", async () => {
  const button = $("#generate"); button.disabled = true; set("#request-state", "requesting…");
  try {
    const prompt = $("#prompt").value;
    const maxNewTokens = Number($("#max-tokens").value);
    const temperature = Number($("#temperature").value);
    const response = await fetch("/api/generate", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ prompt, max_new_tokens: maxNewTokens, temperature }) });
    if (!response.ok) throw new Error(await errorMessage(response, "Generation request failed"));
    const replay = await response.json();
    const order = Number(replay.context_order || state.metrics?.behavior?.order || 0);
    const probabilityResponse = await fetch("/api/probabilities", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ context: prompt.slice(-order) }) });
    if (!probabilityResponse.ok) throw new Error(await errorMessage(probabilityResponse, "Probability request failed"));
    const probabilityPayload = await probabilityResponse.json();
    if (replay.trace?.[0]) replay.trace[0].candidates = probabilityPayload.candidates;
    renderReplay(replay); set("#request-state", "complete");
  } catch (error) { set("#generated", `Request error: ${error.message}`); set("#request-state", "error"); showError(error.message); }
  finally { button.disabled = false; }
});
load();
