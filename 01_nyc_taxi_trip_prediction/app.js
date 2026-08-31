const fallbackMetrics = {
  rows_after_cleaning: 5939,
  train_rows: 4752,
  test_rows: 1187,
  baseline_median_seconds: 576,
  baseline: { mae_seconds: 143.727, rmse_seconds: 176.635, r2: -0.0033 },
  linear_log_target: { mae_seconds: 81.732, rmse_seconds: 102.373, r2: 0.663 },
  source: "deterministic synthetic NYC-like fallback"
};

let metrics = fallbackMetrics;

const $all = (selector) => [...document.querySelectorAll(selector)];
const setMetric = (key, value) => $all(`[data-metric="${key}"]`).forEach((node) => { node.textContent = value; });
const formatNumber = (value, digits = 3) => Number(value).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });

function renderMetrics(next) {
  metrics = next;
  const model = metrics.linear_log_target;
  const baseline = metrics.baseline;
  const improvement = ((baseline.mae_seconds - model.mae_seconds) / baseline.mae_seconds) * 100;
  const maeDelta = baseline.mae_seconds - model.mae_seconds;
  setMetric("model-mae", formatNumber(model.mae_seconds));
  setMetric("baseline-mae", formatNumber(baseline.mae_seconds));
  setMetric("improvement", improvement.toFixed(1));
  setMetric("r2", Number(model.r2).toFixed(4));
  setMetric("rows", Number(metrics.rows_after_cleaning).toLocaleString());
  setMetric("split", `${Number(metrics.train_rows).toLocaleString()} / ${Number(metrics.test_rows).toLocaleString()}`);
  setMetric("mae-delta", formatNumber(maeDelta));
  $all("[data-source]").forEach((node) => { node.textContent = metrics.source || fallbackMetrics.source; });
  const heroOrbit = document.querySelector(".hero-orbit");
  if (heroOrbit) heroOrbit.setAttribute("aria-label", `Experiment result: model MAE ${formatNumber(model.mae_seconds)} seconds`);
  const baselineBar = document.querySelector(".bar-baseline");
  const modelBar = document.querySelector(".bar-model");
  if (baselineBar && modelBar) {
    baselineBar.style.width = "100%";
    modelBar.style.width = `${Math.max(8, (model.mae_seconds / baseline.mae_seconds) * 100)}%`;
  }
}

function haversineMiles(lat1, lon1, lat2, lon2) {
  const rad = Math.PI / 180;
  const dLat = (lat2 - lat1) * rad;
  const dLon = (lon2 - lon1) * rad;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
  return 3958.8 * 2 * Math.asin(Math.sqrt(Math.max(0, Math.min(1, a))));
}

function drawEstimateChart(seconds, isRush) {
  const svg = document.querySelector("#estimate-chart");
  const points = Array.from({ length: 7 }, (_, index) => {
    const x = 20 + index * 80;
    const wave = Math.sin(index * 1.1) * 7;
    const factor = 0.65 + index * 0.055;
    return [x, 103 - Math.min(63, (seconds / 720) * 63 * factor) + wave];
  });
  const polyline = points.map(([x, y]) => `${x},${y}`).join(" ");
  const area = `20,112 ${polyline} 500,112`;
  const [lastX, lastY] = points[points.length - 1];
  svg.innerHTML = `<line class="chart-gridline" x1="20" y1="39" x2="500" y2="39" /><line class="chart-gridline" x1="20" y1="76" x2="500" y2="76" /><path class="chart-area" d="M${area}Z" /><polyline class="chart-line" points="${polyline}" /><circle class="chart-point" cx="${lastX}" cy="${lastY}" r="5" /><text class="chart-label" x="20" y="126">pickup</text><text class="chart-label" x="448" y="126">drop-off</text><text class="chart-label" x="405" y="20">${isRush ? "rush-hour lift" : "off-peak baseline"}</text>`;
}

function updateEstimate(event) {
  if (event) event.preventDefault();
  const form = new FormData(document.querySelector("#estimator-form"));
  const pickupLon = Number(form.get("pickupLongitude"));
  const pickupLat = Number(form.get("pickupLatitude"));
  const dropoffLon = Number(form.get("dropoffLongitude"));
  const dropoffLat = Number(form.get("dropoffLatitude"));
  const passengers = Number(form.get("passengers"));
  const pickup = new Date(form.get("pickupTime"));
  const distance = haversineMiles(pickupLat, pickupLon, dropoffLat, dropoffLon);
  const hour = pickup.getHours();
  const isRush = [7, 8, 9, 16, 17, 18, 19].includes(hour);
  const isWeekend = [0, 6].includes(pickup.getDay());
  const seconds = Math.max(60, Math.round(240 + 115 * distance + (isRush ? 90 : 0) + 25 * Math.max(0, passengers - 1) + (isWeekend ? -12 : 0)));
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  document.querySelector("#estimate-value").textContent = `${mins}:${secs}`;
  document.querySelector("#distance-value").textContent = distance.toFixed(1);
  document.querySelector("#context-value").textContent = isRush ? "rush-hour" : "off-peak";
  document.querySelector("#rush-status").textContent = isRush ? "rush hour" : "off-peak";
  document.querySelector("#rush-status").classList.toggle("quiet", !isRush);
  document.querySelector("#estimate-summary").textContent = `A ${distance.toFixed(1)} mi trip with ${passengers} passenger${passengers === 1 ? "" : "s"}, leaving ${isRush ? "during the evening commute" : "outside the rush-hour window"}.`;
  drawEstimateChart(seconds, isRush);
}

async function loadOutputs() {
  try {
    const response = await fetch("outputs/metrics.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderMetrics(await response.json());
    document.querySelector("#data-status").textContent = "metrics loaded from outputs/metrics.json";
  } catch (error) {
    renderMetrics(fallbackMetrics);
    document.querySelector("#data-status").textContent = "preview values · serve folder to load JSON";
  }
}

document.querySelector("#estimator-form").addEventListener("submit", updateEstimate);
document.querySelector("#estimator-form").addEventListener("input", updateEstimate);
$all(".copy-button").forEach((button) => button.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(button.dataset.copy);
    button.textContent = "copied";
    setTimeout(() => { button.textContent = "copy"; }, 1200);
  } catch { button.textContent = "select"; }
}));

renderMetrics(fallbackMetrics);
updateEstimate();
loadOutputs();
