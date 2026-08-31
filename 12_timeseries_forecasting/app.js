const formatMetric = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(3) : "—";

const horizonCopy = {
  6: ["6 months · near-term lens", "First six months of the held-out test forecast."],
  12: ["12 months · one seasonal cycle", "First twelve months of the held-out test forecast."],
  24: ["24 months · two seasonal cycles", "First twenty-four months of the held-out test forecast."],
  36: ["36 months · full test window", "The full reported test forecast from the current artifact run."],
};

let metricsData = null;
let selectedHorizon = 12;

function setText(id, value) { const node = document.getElementById(id); if (node) node.textContent = value; }

function setHorizon(value) {
  selectedHorizon = Number(value) || 12;
  value = selectedHorizon;
  const [label, description] = horizonCopy[value] || horizonCopy[12];
  setText("horizonLabel", label); setText("horizonDescription", description);
  setText("testWindow", `${value} MONTHS`);
  const marker = document.getElementById("horizonMarker");
  if (marker) marker.style.left = `${Math.max(0, Math.min(100, (Number(value) / 36) * 100))}%`;
  document.querySelectorAll(".horizon-button").forEach((button) => {
    const active = button.dataset.horizon === String(value);
    button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active));
  });
  if (!metricsData) return;
  const horizon = metricsData.horizon_metrics?.[String(value)];
  if (!horizon) return;
  updateMetricCards(horizon);
  const artifact = metricsData.forecast_artifacts?.[String(value)];
  const image = document.getElementById("forecastImage");
  if (image && artifact) {
    image.src = `outputs/${artifact}`;
    image.alt = `Observed monthly values with aligned seasonal-naive and gradient-boosting forecasts through the first ${value} test months; dotted lines mark the forecast origin and test start.`;
    setText("forecastArtifact", `${artifact} · source artifact`);
  }
}

function updateMetricCards(block) {
  const baseline = block.baseline_seasonal_naive || {};
  const model = block.model_hist_gradient_boosting || {};
  const baselineMae = Number(baseline.mae);
  const modelMae = Number(model.mae);
  setText("baselineMae", formatMetric(baselineMae)); setText("baselineRmse", formatMetric(baseline.rmse));
  setText("modelMae", formatMetric(modelMae)); setText("modelRmse", formatMetric(model.rmse));
  if (!Number.isFinite(baselineMae) || !Number.isFinite(modelMae)) return;
  const baselineWins = baselineMae <= modelMae;
  const winner = baselineWins ? "Seasonal naive" : "Hist. gradient boosting";
  const delta = modelMae === 0 ? 0 : Math.abs((1 - baselineMae / modelMae) * 100);
  setText("winnerName", winner);
  setText("winnerText", `is the lower-error forecaster on this ${selectedHorizon}-month lens.`);
  setText("outcomeHeading", baselineWins ? "Baseline leads" : "Model leads");
  setText("baselineBadge", baselineWins ? "lower MAE" : "test result");
  setText("modelBadge", baselineWins ? "test result" : "lower MAE");
  setText("deltaHeading", baselineWins ? "Reference advantage" : "Model advantage");
  setText("deltaDescription", baselineWins ? "lower error for seasonal naive vs. the fixed model configuration" : "lower error for the fixed model configuration vs. seasonal naive");
  setText("deltaValue", `${delta.toFixed(1)}%`);
  const bar = document.getElementById("deltaBar"); if (bar) bar.style.width = `${Math.min(100, delta)}%`;
}

async function loadMetrics() {
  try {
    const response = await fetch("outputs/metrics.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`metrics.json returned ${response.status}`);
    const data = await response.json();
    metricsData = data;
    setText("heroRows", data.dataset_rows ?? "—"); setText("splitRows", data.dataset_rows ?? "—");
    setText("artifactStatus", "Metrics + forecast slice connected");
    setHorizon(selectedHorizon);
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
