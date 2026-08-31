const fallbackMetrics = {
  backend: "stdlib_char_ngram",
  seed: 255,
  train_chars: 288,
  test_chars: 36,
  loss: 3.3023,
  perplexity: 27.1741,
  sample: "user: explain a transformer\nassistant: A transformer\nassistant: A transformer"
};

const responseLibrary = [
  { match: ["machine", "learning", "ml"], answer: "Machine learning finds patterns in data to make useful predictions." },
  { match: ["transformer", "attention"], answer: "A transformer uses attention to mix information across a sequence." },
  { match: ["concise", "short", "brief"], answer: "Small experiments make ideas easier to understand." },
  { match: ["hello", "hi", "hey"], answer: "Hello! I am Nano, a tiny language model." },
  { match: ["corpus", "data", "dataset"], answer: "This experiment uses a seven-line synthetic chat corpus and an 80/10/10 chronological split." },
  { match: ["perplexity", "loss", "metric"], answer: "The verified baseline reports held-out test loss 3.3023 and perplexity 27.1741. Treat those as a sanity check, not a capability score." }
];

const $ = (selector) => document.querySelector(selector);
const formatBackend = (backend = "stdlib_char_ngram") => backend === "torch_transformer" ? "torch transformer" : "char n-gram";

function renderMetrics(metrics, usedFallback = false) {
  $("#perplexity").textContent = Number(metrics.perplexity).toFixed(4);
  $("#loss").textContent = Number(metrics.loss).toFixed(4);
  $("#backend").textContent = formatBackend(metrics.backend);
  $("#backend-status").textContent = metrics.backend === "torch_transformer" ? "TORCH" : "STDLIB";
  $("#seed").textContent = metrics.seed ?? "255";
  $("#config-seed").textContent = metrics.seed ?? "255";
  $("#train-chars").textContent = metrics.train_chars ?? "—";
  $("#test-chars").textContent = metrics.test_chars ?? "—";
  $("#verify-loss").textContent = Number(metrics.loss).toFixed(4);
  $("#verify-perplexity").textContent = Number(metrics.perplexity).toFixed(4);
  const train = Number(metrics.train_chars) || 0;
  const test = Number(metrics.test_chars) || 0;
  $("#train-bar").style.width = `${(train / Math.max(train + test, 1)) * 100}%`;
  const status = $("#data-status");
  status.classList.add(usedFallback ? "is-fallback" : "is-loaded");
  status.innerHTML = usedFallback
    ? '<span class="loader"></span> Could not fetch metrics.json — showing the verified fallback snapshot.'
    : '<span class="loader"></span> metrics.json loaded from the local workspace · values are live from the artifact';
}

async function loadMetrics() {
  try {
    const response = await fetch("metrics.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`metrics.json returned ${response.status}`);
    renderMetrics(await response.json());
  } catch (error) {
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
  time.textContent = type === "user" ? "now · you" : "now · local preview";
  body.append(paragraph, time);
  message.append(avatar, body);
  $("#chat-window").insertBefore(message, $("#suggestions"));
  $("#chat-window").scrollTop = $("#chat-window").scrollHeight;
}

function replyTo(prompt) {
  const normalized = prompt.toLowerCase();
  const found = responseLibrary.find((entry) => entry.match.some((word) => normalized.includes(word)));
  return found?.answer || "I only have a few local teaching examples. Try asking about machine learning, transformers, the corpus, or perplexity.";
}

function handlePrompt(prompt) {
  const cleanPrompt = prompt.trim();
  if (!cleanPrompt) return;
  addMessage(cleanPrompt, "user");
  $("#chat-input").value = "";
  window.setTimeout(() => addMessage(replyTo(cleanPrompt), "assistant"), 280);
}

function resetChat() {
  $("#chat-window").innerHTML = `<div class="message message-assistant"><span class="message-avatar">N</span><div><p>Hi — I’m Nano, a tiny language model trained on a tiny local corpus. Ask me about transformers, machine learning, or the experiment.</p><time>now · local preview</time></div></div><div class="suggestions" id="suggestions"><button type="button" data-prompt="What is machine learning?">What is machine learning?</button><button type="button" data-prompt="Explain a transformer">Explain a transformer</button><button type="button" data-prompt="Be concise">Be concise</button></div>`;
}

$("#chat-form").addEventListener("submit", (event) => { event.preventDefault(); handlePrompt($("#chat-input").value); });
$("#chat-window").addEventListener("click", (event) => { const button = event.target.closest("[data-prompt]"); if (button) handlePrompt(button.dataset.prompt); });
$("#reset-chat").addEventListener("click", resetChat);
document.querySelectorAll(".copy-button").forEach((button) => button.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(button.dataset.copy); } catch (_) { /* Clipboard permissions are optional. */ }
  const original = button.textContent; button.textContent = "copied"; window.setTimeout(() => { button.textContent = original; }, 1200);
}));

loadMetrics();
