const formatMetric = (value) => Number.isFinite(value) ? value.toFixed(3) : "—";

const horizonCopy = {
  6: ["6 months · near-term lens", "Illustrative view of the first half-year inside the held-out window."],
  12: ["12 months · one seasonal cycle", "Illustrative planning view across a complete annual pattern."],
  24: ["24 months · two seasonal cycles", "Illustrative planning view across two annual patterns."],
  36: ["36 months · full test window", "The full reported test horizon from the current artifact run."],
};

function setText(id, value) { const node = document.getElementById(id); if (node) node.textContent = value; }

function setHorizon(value) {
  const [label, description] = horizonCopy[value] || horizonCopy[12];
  setText("horizonLabel", label); setText("horizonDescription", description);
  const marker = document.getElementById("horizonMarker");
  if (marker) marker.style.left = `${Math.max(0, Math.min(100, (Number(value) / 36) * 100))}%`;
  document.querySelectorAll(".horizon-button").forEach((button) => {
    const active = button.dataset.horizon === String(value);
    button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active));
  });
}

async function loadMetrics() {
  try {
    const response = await fetch("outputs/metrics.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`metrics.json returned ${response.status}`);
    const data = await response.json();
    const baseline = data.baseline_seasonal_naive || {}; const model = data.model_hist_gradient_boosting || {};
    const testMonths = Number.isFinite(Number(data.split?.test_start)) && Number.isFinite(Number(data.dataset_rows)) ? Number(data.dataset_rows) - Number(data.split.test_start) : 36;
    const advantage = Number.isFinite(baseline.mae) && Number.isFinite(model.mae) ? Math.max(0, (1 - baseline.mae / model.mae) * 100) : null;
    setText("heroRows", data.dataset_rows ?? "—"); setText("splitRows", data.dataset_rows ?? "—");
    setText("baselineMae", formatMetric(baseline.mae)); setText("baselineRmse", formatMetric(baseline.rmse));
    setText("modelMae", formatMetric(model.mae)); setText("modelRmse", formatMetric(model.rmse));
    setText("deltaValue", advantage === null ? "—" : `${advantage.toFixed(1)}%`); setText("testWindow", `${testMonths} MONTHS`); setText("artifactStatus", "Metrics + plot connected");
    const bar = document.getElementById("deltaBar"); if (bar && advantage !== null) bar.style.width = `${Math.min(100, advantage)}%`;
  } catch (error) {
    setText("artifactStatus", "Open via a local server to load metrics"); document.getElementById("artifactStatus")?.classList.add("load-error");
    console.warn("Forecasting Studio could not load outputs/metrics.json.", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setHorizon(12);
  document.querySelectorAll(".horizon-button").forEach((button) => button.addEventListener("click", () => setHorizon(button.dataset.horizon)));
  loadMetrics();
});
