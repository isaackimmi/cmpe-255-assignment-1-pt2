const formatMetric = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(3) : "—";
const formatDate = (date) => {
  const parsed = new Date(`${date}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? date : parsed.toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
};

const horizonCopy = {
  6: ["6 months · near-term lens", "Cumulative test prefix: months 1–6."],
  12: ["12 months · one seasonal cycle", "Cumulative test prefix: months 1–12."],
  24: ["24 months · two seasonal cycles", "Cumulative test prefix: months 1–24."],
  36: ["36 months · full test slice", "Cumulative test prefix: months 1–36."],
};

let metricsData = null;
let forecastRows = [];
let selectedHorizon = 12;

function setText(id, value) { const node = document.getElementById(id); if (node) node.textContent = value; }

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(",");
  return lines.map((line) => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((header, index) => [header, values[index]]));
  }).map((row) => Object.fromEntries(Object.entries(row).map(([key, value]) => {
    if (["actual", "baseline_seasonal_naive", "model_hist_gradient_boosting", "baseline_residual", "model_residual", "baseline_absolute_error", "model_absolute_error"].includes(key)) return [key, Number(value)];
    if (["forecast_lead", "test_prefix_month"].includes(key)) return [key, value === "" ? null : Number(value)];
    return [key, value];
  })));
}

function linePath(points, x, y, key) {
  return points.map((row, index) => `${index ? "L" : "M"}${x(index).toFixed(2)} ${y(row[key]).toFixed(2)}`).join(" ");
}

function drawForecastChart(rows, horizon) {
  const svg = document.getElementById("forecastChart");
  if (!svg || !rows.length) return;
  const validationRows = rows.filter((row) => row.split === "validation");
  const visible = rows.filter((row) => row.split === "validation" || Number(row.test_prefix_month) <= horizon);
  const values = visible.flatMap((row) => [row.actual, row.baseline_seasonal_naive, row.model_hist_gradient_boosting]);
  const width = 900, height = 360, left = 50, right = 18, top = 24, bottom = 40;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const min = Math.min(...values), max = Math.max(...values), pad = Math.max(1, (max - min) * 0.12);
  const y = (value) => top + ((max + pad - value) / (max - min + (pad * 2))) * plotHeight;
  const x = (index) => left + (visible.length === 1 ? plotWidth / 2 : index / (visible.length - 1) * plotWidth);
  const testX = x(validationRows.length - 0.5);
  const first = visible[0]?.date, last = visible[visible.length - 1]?.date;
  svg.innerHTML = `
    <title>Actual values and recursive forecasts through ${horizon} test months</title>
    <desc>Rows are loaded from forecast_predictions.csv. The vertical dotted line is the common forecast origin; the dashed line is the nominal test boundary.</desc>
    <g class="chart-grid"><line x1="${left}" y1="${top + plotHeight / 2}" x2="${width - right}" y2="${top + plotHeight / 2}" /><line x1="${left}" y1="${top + plotHeight}" x2="${width - right}" y2="${top + plotHeight}" /></g>
    <line class="chart-origin" x1="${x(0)}" y1="${top}" x2="${x(0)}" y2="${top + plotHeight}" /><text class="chart-marker-label" x="${x(0) + 6}" y="${top + 12}">origin</text>
    ${horizon >= validationRows.length ? `<line class="chart-test-boundary" x1="${testX}" y1="${top}" x2="${testX}" y2="${top + plotHeight}" /><text class="chart-marker-label" x="${testX + 6}" y="${top + 27}">test start</text>` : ""}
    <path class="chart-line actual-line" d="${linePath(visible, x, y, "actual")}" /><path class="chart-line baseline-line" d="${linePath(visible, x, y, "baseline_seasonal_naive")}" /><path class="chart-line model-line" d="${linePath(visible, x, y, "model_hist_gradient_boosting")}" />
    <text class="chart-axis-label" x="${left}" y="${height - 12}">${formatDate(first)}</text><text class="chart-axis-label" text-anchor="end" x="${width - right}" y="${height - 12}">${formatDate(last)}</text>
    <text class="chart-axis-label" x="8" y="${top + 4}">${formatMetric(max + pad)}</text><text class="chart-axis-label" x="8" y="${top + plotHeight}">${formatMetric(min - pad)}</text>`;
  svg.setAttribute("aria-label", `Actual values and seasonal-naive and model forecasts through ${horizon} test months, from ${first} to ${last}`);
}

function drawErrorChart(rows) {
  const svg = document.getElementById("errorChart");
  if (!svg || !rows.length) return;
  const width = 900, height = 230, left = 36, right = 15, top = 20, bottom = 28;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const maxAbs = Math.max(1, ...rows.flatMap((row) => [Math.abs(row.baseline_residual), Math.abs(row.model_residual)]));
  const zero = top + plotHeight / 2;
  const x = (index) => left + (index + 0.5) / rows.length * plotWidth;
  const barWidth = Math.max(2, Math.min(10, plotWidth / rows.length / 3));
  const bar = (value, index, color, offset) => {
    const heightValue = Math.abs(value) / maxAbs * (plotHeight / 2 - 5);
    const y = value >= 0 ? zero - heightValue : zero;
    return `<rect x="${(x(index) - barWidth + offset * barWidth).toFixed(2)}" y="${y.toFixed(2)}" width="${barWidth}" height="${heightValue.toFixed(2)}" fill="${color}" opacity=".85"><title>${value.toFixed(3)}</title></rect>`;
  };
  svg.innerHTML = `<title>Residual comparison for selected test prefix</title><desc>Positive residuals mean actual was above the forecast. Each month shows seasonal-naive and model residuals.</desc><line class="error-zero" x1="${left}" y1="${zero}" x2="${width - right}" y2="${zero}" /><text class="chart-axis-label" x="4" y="${top + 4}">high</text><text class="chart-axis-label" x="4" y="${height - bottom}">low</text>${rows.map((row, index) => `${bar(row.baseline_residual, index, "#ee8754", 0)}${bar(row.model_residual, index, "#157e78", 1)}`).join("")}<text class="chart-axis-label" x="${left}" y="${height - 8}">${formatDate(rows[0].date)}</text><text class="chart-axis-label" text-anchor="end" x="${width - right}" y="${height - 8}">${formatDate(rows[rows.length - 1].date)}</text>`;
}

function renderTable(rows) {
  const body = document.getElementById("forecastRows");
  if (!body) return;
  body.replaceChildren();
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    [formatDate(row.date), `L${row.forecast_lead}`, formatMetric(row.actual), formatMetric(row.baseline_seasonal_naive), formatMetric(row.model_hist_gradient_boosting), formatMetric(row.baseline_residual), formatMetric(row.model_residual)].forEach((value) => {
      const td = document.createElement("td"); td.textContent = value; tr.appendChild(td);
    });
    body.appendChild(tr);
  });
  setText("tableCount", `${rows.length} rows`);
}

function updateMetricCards(block) {
  const baseline = block.baseline_seasonal_naive || {}, model = block.model_hist_gradient_boosting || {};
  const baselineMae = Number(baseline.mae), modelMae = Number(model.mae);
  setText("baselineMae", formatMetric(baselineMae)); setText("baselineRmse", formatMetric(baseline.rmse));
  setText("modelMae", formatMetric(modelMae)); setText("modelRmse", formatMetric(model.rmse));
  if (!Number.isFinite(baselineMae) || !Number.isFinite(modelMae)) return;
  const baselineWins = baselineMae <= modelMae;
  const winner = baselineWins ? "Seasonal naive" : "Hist. gradient boosting";
  const delta = modelMae === 0 ? 0 : Math.abs((1 - baselineMae / modelMae) * 100);
  setText("winnerName", winner); setText("winnerText", `is the lower-error forecaster on this ${selectedHorizon}-month prefix.`);
  setText("outcomeHeading", baselineWins ? "Baseline leads" : "Model leads");
  setText("baselineBadge", baselineWins ? "lower MAE" : "test result"); setText("modelBadge", baselineWins ? "test result" : "lower MAE");
  setText("deltaHeading", baselineWins ? "Reference advantage" : "Model advantage");
  setText("deltaDescription", baselineWins ? "lower error for seasonal naive vs. the fixed model configuration" : "lower error for the fixed model configuration vs. seasonal naive");
  setText("deltaValue", `${delta.toFixed(1)}%`);
  const bar = document.getElementById("deltaBar"); if (bar) bar.style.width = `${Math.min(100, delta)}%`;
}

function setHorizon(value) {
  selectedHorizon = Number(value) || 12;
  const [label, description] = horizonCopy[selectedHorizon] || horizonCopy[12];
  setText("horizonLabel", label); setText("horizonDescription", description); setText("testWindow", selectedHorizon); setText("noteHorizon", selectedHorizon);
  const marker = document.getElementById("horizonMarker"); if (marker) marker.style.left = `${Math.max(0, Math.min(100, (selectedHorizon / 36) * 100))}%`;
  document.querySelectorAll(".horizon-button").forEach((button) => { const active = button.dataset.horizon === String(selectedHorizon); button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active)); });
  if (!metricsData || !forecastRows.length) return;
  const horizon = metricsData.horizon_metrics?.[String(selectedHorizon)];
  if (horizon) updateMetricCards(horizon);
  const testRows = forecastRows.filter((row) => row.split === "test" && row.test_prefix_month <= selectedHorizon);
  drawForecastChart(forecastRows, selectedHorizon); drawErrorChart(testRows); renderTable(testRows);
  const artifact = metricsData.forecast_artifacts?.[String(selectedHorizon)];
  const artifactLink = document.getElementById("forecastArtifact");
  if (artifactLink && artifact) { artifactLink.href = `outputs/${artifact}`; artifactLink.textContent = `${artifact} · source artifact`; }
  const first = testRows[0]?.date, last = testRows.at(-1)?.date;
  setText("errorRange", first && last ? `${formatDate(first)} → ${formatDate(last)}` : "—");
}

async function sha256(buffer) {
  if (!globalThis.crypto?.subtle) return null;
  const hash = await crypto.subtle.digest("SHA-256", buffer);
  return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function verifyManifest(manifest) {
  if (!manifest?.artifacts) return "artifact loaded · no manifest";
  if (!globalThis.crypto?.subtle) return "artifact loaded · hash check unavailable";
  for (const [name, expected] of Object.entries(manifest.artifacts)) {
    const response = await fetch(`outputs/${name}`, { cache: "no-store" });
    if (!response.ok || await sha256(await response.arrayBuffer()) !== expected.sha256) return "artifact mismatch";
  }
  return "artifact integrity matched";
}

async function loadMetrics() {
  try {
    const [metricsResponse, csvResponse, manifestResponse] = await Promise.all([
      fetch("outputs/metrics.json", { cache: "no-store" }), fetch("outputs/forecast_predictions.csv", { cache: "no-store" }), fetch("outputs/artifact_manifest.json", { cache: "no-store" }),
    ]);
    if (!metricsResponse.ok) throw new Error(`metrics.json returned ${metricsResponse.status}`);
    if (!csvResponse.ok) throw new Error(`forecast_predictions.csv returned ${csvResponse.status}`);
    metricsData = await metricsResponse.json(); forecastRows = parseCsv(await csvResponse.text());
    const manifest = manifestResponse.ok ? await manifestResponse.json() : null;
    setText("heroRows", metricsData.dataset_rows ?? "—"); setText("splitRows", metricsData.dataset_rows ?? "—");
    if (manifest) {
      const checkout = manifest.repository_dirty ? "dirty checkout" : "clean checkout";
      setText("provenanceStatus", `${manifest.source_revision || "unknown revision"} · ${checkout} · ${manifest.generated_at_utc || "generation time unavailable"}`);
    } else {
      setText("provenanceStatus", "manifest unavailable");
    }
    setText("artifactStatus", await verifyManifest(manifest)); document.getElementById("artifactStatus")?.classList.remove("load-error");
    setHorizon(selectedHorizon);
  } catch (error) {
    setText("artifactStatus", "artifact load failed"); document.getElementById("artifactStatus")?.classList.add("load-error");
    console.warn("Forecasting Studio could not load generated artifacts.", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setHorizon(12);
  document.querySelectorAll(".horizon-button").forEach((button) => button.addEventListener("click", () => setHorizon(button.dataset.horizon)));
  loadMetrics();
});
