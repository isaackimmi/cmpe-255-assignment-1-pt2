const fallbackVocabulary = ["\n", " ", "!", ",", ".", ":", "<UNK>", "?", "A", "H", "I", "M", "N", "a", "b", "c", "d", "e", "f", "g", "h", "i", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "w", "x", "y"];
const fallbackDistribution = fallbackVocabulary.map((token) => ({ token, probability: 1 / fallbackVocabulary.length, count: 0 }));

const fallbackMetrics = {
  backend: "stdlib_char_ngram",
  seed: 255,
  train_chars: 288,
  test_chars: 36,
  loss: 3.3023,
  perplexity: 27.1741,
  split: { train_chars: 288, validation_chars: 36, test_chars: 36, train_fraction: 0.8, validation_fraction: 0.1, test_fraction: 0.1 },
  dataset: { name: "tiny_corpus.txt", characters: 360, lines: 8, dialogue_pairs: 4, synthetic: true },
  validation: { loss: 2.9446, perplexity: 19.0026, target_chars: 36, oov_count: 1, oov_rate: 0.0278 },
  test: { loss: 3.3023, perplexity: 27.1741, target_chars: 36, oov_count: 0, oov_rate: 0 },
  oov_counts: { train: 0, validation: 1, test: 0 },
  vocabulary: fallbackVocabulary,
  vocab_size: fallbackVocabulary.length,
  config: { order: 3, alpha: 0.2, train_fraction: 0.8, validation_fraction: 0.1, device: "auto", output: "metrics.json" },
  behavior: { kind: "deterministic_replay", backend: "stdlib_char_ngram", order: 3, temperature: 0, max_new_tokens: 24, deterministic: true, vocabulary: fallbackVocabulary, default_distribution: fallbackDistribution, contexts: {} },
  verification: { summary: "run test suite locally", note: "Fallback snapshot; no test result is inferred." },
};

let activeMetrics = fallbackMetrics;
const $ = (selector) => document.querySelector(selector);
const formatBackend = (backend = "stdlib_char_ngram") => backend === "torch_transformer" ? "torch transformer" : "char n-gram";
const formatValue = (value, digits = 4) => Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "—";
const formatFraction = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "—";
const formatToken = (token) => token === "\n" ? "↵" : token === " " ? "␠" : token === "<UNK>" ? "<UNK>" : token;
const config = () => activeMetrics.config || {};

function renderMetrics(metrics, usedFallback = false) {
  activeMetrics = metrics;
  const split = metrics.split || {};
  const validation = metrics.validation || {};
  const test = metrics.test || {};
  const oov = metrics.oov_counts || {};
  const total = [split.train_chars, split.validation_chars, split.test_chars].reduce((sum, value) => sum + (Number(value) || 0), 0) || 1;
  const backend = metrics.backend || config().backend || "stdlib_char_ngram";
  const backendConfig = config();
  const contextSize = backend === "torch_transformer" ? backendConfig.block_size : backendConfig.order;

  $("#perplexity").textContent = formatValue(test.perplexity ?? metrics.perplexity);
  $("#loss").textContent = formatValue(test.loss ?? metrics.loss);
  $("#backend").textContent = formatBackend(backend);
  $("#backend-status").textContent = backend === "torch_transformer" ? "TORCH" : "STDLIB";
  $("#backend-caption").textContent = backend === "torch_transformer" ? "optional causal Transformer" : "dependency-free baseline";
  $("#perplexity-caption").textContent = `${test.target_chars ?? split.test_chars ?? "—"}-character conditional test`;
  $("#seed").textContent = metrics.seed ?? "—";
  $("#config-seed").textContent = metrics.seed ?? "—";
  $("#train-chars").textContent = split.train_chars ?? metrics.train_chars ?? "—";
  $("#validation-chars").textContent = split.validation_chars ?? "—";
  $("#test-chars").textContent = split.test_chars ?? metrics.test_chars ?? "—";
  $("#test-oov").textContent = `${oov.test ?? test.oov_count ?? "—"} (${formatValue(test.oov_rate, 2)})`;
  $("#validation-oov").textContent = `${oov.validation ?? validation.oov_count ?? "—"} (${formatValue(validation.oov_rate, 2)})`;
  $("#verify-loss").textContent = formatValue(test.loss ?? metrics.loss);
  $("#verify-perplexity").textContent = formatValue(test.perplexity ?? metrics.perplexity);
  $("#verify-tests").textContent = metrics.verification?.summary || "run test suite locally";
  $("#train-bar").style.width = `${((Number(split.train_chars) || 0) / total) * 100}%`;
  $("#validation-bar").style.width = `${((Number(split.validation_chars) || 0) / total) * 100}%`;
  $("#test-bar").style.width = `${((Number(split.test_chars) || 0) / total) * 100}%`;

  $("#dataset-lines").textContent = metrics.dataset ? `${metrics.dataset.lines} lines · ${metrics.dataset.dialogue_pairs} pairs` : "—";
  $("#dataset-source").textContent = metrics.dataset ? `${metrics.dataset.name} · synthetic` : "—";
  $("#backend-mode").textContent = `${formatBackend(backend)} · ${metrics.behavior?.kind || "artifact"}`;
  $("#config-backend").textContent = backend;
  $("#config-order").innerHTML = `${contextSize ?? "—"} <small>${backend === "torch_transformer" ? "block size" : "context chars"}</small>`;
  $("#config-train-fraction").textContent = formatFraction(split.train_fraction ?? backendConfig.train_fraction);
  $("#config-validation-fraction").textContent = formatFraction(split.validation_fraction ?? backendConfig.validation_fraction);
  $("#config-test-fraction").textContent = formatFraction(split.test_fraction);
  $("#config-smoothing").innerHTML = backend === "torch_transformer"
    ? `${backendConfig.lr ?? "—"} <small>learning rate</small>`
    : `${backendConfig.alpha ?? "—"} <small>smoothing</small>`;
  $("#config-device").textContent = metrics.device || backendConfig.device || "—";
  $("#config-vocab").textContent = `${metrics.vocab_size ?? metrics.vocabulary?.length ?? "—"} tokens · ${oov.validation ?? validation.oov_count ?? 0} val OOV`;
  $("#config-test-evals").textContent = metrics.test_evaluations ?? "—";
  $("#config-callout").textContent = backend === "torch_transformer"
    ? "This page is showing a serialized Transformer trace. The test score was recorded after validation checkpoint selection."
    : "This page is showing serialized smoothed next-character distributions. The test score is conditional on the preceding ground-truth context and was evaluated once.";

  const status = $("#data-status");
  status.classList.toggle("is-fallback", usedFallback);
  status.classList.toggle("is-loaded", !usedFallback);
  status.innerHTML = usedFallback
    ? '<span class="loader"></span> Could not fetch metrics.json — showing the verified fallback snapshot.'
    : '<span class="loader"></span> metrics.json loaded from the local workspace · behavior and metrics are artifact-backed';
  renderInspector(null);
}

async function loadMetrics() {
  try {
    const response = await fetch("metrics.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`metrics.json returned ${response.status}`);
    renderMetrics(await response.json());
  } catch (_) {
    renderMetrics(fallbackMetrics, true);
  }
}

function addMessage(text, type) {
  const message = document.createElement("div");
  message.className = `message message-${type}`;
  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.textContent = type === "user" ? "Y" : "N";
  const body = document.createElement("div");
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  const time = document.createElement("time");
  time.textContent = type === "user" ? "now · you" : "now · serialized replay";
  body.append(paragraph, time);
  message.append(avatar, body);
  $("#chat-window").insertBefore(message, $("#suggestions"));
  $("#chat-window").scrollTop = $("#chat-window").scrollHeight;
}

function sortCandidates(candidates = []) {
  return [...candidates].sort((left, right) => Number(right.probability) - Number(left.probability) || String(left.token).localeCompare(String(right.token)));
}

function replayFromNGram(prompt, behavior) {
  const order = Number(behavior.order) || 0;
  const vocabulary = behavior.vocabulary || [];
  const known = new Set(vocabulary);
  const encode = (value) => Array.from(value).map((character) => known.has(character) ? character : "<UNK>");
  const distributionFor = (text) => {
    const encoded = encode(text);
    const key = JSON.stringify(order ? encoded.slice(-order) : []);
    return sortCandidates(behavior.contexts?.[key] || behavior.unseen_context_distribution || behavior.default_distribution || []);
  };
  const maxTokens = Math.min(Number(behavior.max_new_tokens) || 0, 80);
  let text = prompt;
  const trace = [];
  for (let step = 1; step <= maxTokens; step += 1) {
    const candidates = distributionFor(text);
    const selected = candidates[0]?.token || "";
    trace.push({ step, context: text.slice(-order), candidates: candidates.slice(0, 8), selected });
    text += selected;
  }
  return { prompt, text, generated: text.slice(prompt.length), trace, deterministic: behavior.deterministic, context_order: order };
}

function replayPrompt(prompt) {
  const behavior = activeMetrics.behavior;
  if (!behavior) return { prompt, text: prompt, generated: "", trace: [], deterministic: false, context_order: 0 };
  if (behavior.kind === "deterministic_replay" && behavior.contexts) return replayFromNGram(prompt, behavior);
  const canonical = behavior.prompt || prompt;
  return {
    ...behavior,
    prompt: canonical,
    trace: behavior.trace || [],
    text: behavior.text || `${canonical}${behavior.generated || ""}`,
    generated: behavior.generated || "",
    requestedPrompt: prompt,
    promptMismatch: prompt !== canonical,
  };
}

function renderProbabilityList(candidates) {
  const container = $("#next-probabilities");
  container.innerHTML = "";
  if (!candidates?.length) {
    container.innerHTML = '<span class="empty-state">No serialized distribution is available.</span>';
    return;
  }
  candidates.slice(0, 8).forEach((candidate) => {
    const row = document.createElement("div");
    row.className = "probability-row";
    const label = document.createElement("span");
    label.className = "probability-token";
    label.textContent = formatToken(candidate.token);
    const track = document.createElement("span");
    track.className = "probability-track";
    const fill = document.createElement("i");
    fill.style.width = `${Math.max(2, Number(candidate.probability) * 100)}%`;
    track.append(fill);
    const value = document.createElement("strong");
    value.textContent = `${(Number(candidate.probability) * 100).toFixed(1)}%`;
    row.append(label, track, value);
    container.append(row);
  });
}

function renderInspector(replay) {
  if (!replay) {
    $("#replay-status").textContent = "WAITING FOR PROMPT";
    $("#replay-context").textContent = "—";
    $("#replay-context-note").textContent = `order ${activeMetrics.behavior?.order ?? "—"}`;
    $("#trace-count").textContent = "0 steps";
    $("#next-probabilities").innerHTML = '<span class="empty-state">Submit a prompt to inspect the distribution.</span>';
    $("#generation-trace").innerHTML = '<span class="empty-state">The selected character and its candidate probabilities will appear here.</span>';
    return;
  }
  const firstStep = replay.trace?.[0];
  $("#replay-status").textContent = replay.promptMismatch ? "SERIALIZED PROMPT" : replay.deterministic ? "DETERMINISTIC" : "REPLAY";
  const context = replay.context_order ? replay.prompt.slice(-replay.context_order) : "";
  $("#replay-context").textContent = firstStep?.context || context || "∅";
  $("#replay-context-note").textContent = `order ${replay.context_order ?? "—"} · next selected ${formatToken(firstStep?.selected || "—")}`;
  $("#trace-count").textContent = `${replay.trace?.length || 0} steps${replay.promptMismatch ? " · canonical artifact trace" : ""}`;
  renderProbabilityList(firstStep?.candidates || []);
  const trace = $("#generation-trace");
  trace.innerHTML = "";
  (replay.trace || []).forEach((step) => {
    const row = document.createElement("div");
    row.className = "trace-row";
    const stepNumber = document.createElement("span");
    stepNumber.className = "trace-step";
    stepNumber.textContent = String(step.step).padStart(2, "0");
    const context = document.createElement("code");
    context.textContent = step.context || "∅";
    const selected = document.createElement("strong");
    selected.textContent = formatToken(step.selected);
    const candidates = document.createElement("span");
    candidates.className = "trace-candidates";
    candidates.textContent = (step.candidates || []).slice(0, 4).map((item) => `${formatToken(item.token)} ${(Number(item.probability) * 100).toFixed(1)}%`).join(" · ");
    row.append(stepNumber, context, selected, candidates);
    trace.append(row);
  });
}

function handlePrompt(prompt) {
  const cleanPrompt = prompt.trim();
  if (!cleanPrompt) return;
  addMessage(cleanPrompt, "user");
  $("#chat-input").value = "";
  const replay = replayPrompt(cleanPrompt);
  addMessage(replay.generated || "(no new characters in this artifact)", "assistant");
  renderInspector(replay);
}

function resetChat() {
  $("#chat-window").innerHTML = '<div class="message message-assistant"><span class="message-avatar">N</span><div><p>Hi — I’m Nano. Enter a prompt and inspect the serialized next-character replay below.</p><time>artifact-backed local replay</time></div></div><div class="suggestions" id="suggestions"><button type="button" data-prompt="user: explain a transformer\nassistant:">Replay transformer prompt</button><button type="button" data-prompt="user: what is machine learning?\nassistant:">Replay machine learning</button><button type="button" data-prompt="hello">Replay hello</button></div>';
  renderInspector(null);
}

$("#chat-form").addEventListener("submit", (event) => { event.preventDefault(); handlePrompt($("#chat-input").value); });
$("#chat-window").addEventListener("click", (event) => { const button = event.target.closest("[data-prompt]"); if (button) handlePrompt(button.dataset.prompt); });
$("#reset-chat").addEventListener("click", resetChat);
document.querySelectorAll(".copy-button").forEach((button) => button.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(button.dataset.copy); } catch (_) { /* Clipboard permissions are optional. */ }
  const original = button.textContent; button.textContent = "copied"; window.setTimeout(() => { button.textContent = original; }, 1200);
}));

loadMetrics();
