const snapshotBody = document.getElementById("snapshot-body");
const snapshotTrust = document.getElementById("snapshot-trust");
const compareBody = document.getElementById("compare-body");
const compareTrust = document.getElementById("compare-trust");
const signalsBody = document.getElementById("signals-body");
const signalsTrust = document.getElementById("signals-trust");
const explanationTrust = document.getElementById("explanation-trust");
const explanationSummary = document.getElementById("explanation-summary");
const explanationPoints = document.getElementById("explanation-points");

let latestSnapshot = null;
let latestSignals = null;

function formatTrust(trust) {
  if (!trust) {
    return "No trust metadata";
  }
  const sources = (trust.sources || [])
    .map((source) => source.source_label || source.source_id)
    .join(", ");
  return `freshness=${trust.freshness_status} | availability=${trust.availability} | degraded=${trust.is_degraded} | sources=${sources || "n/a"}`;
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return Number(value).toFixed(3);
}

async function getJson(path, options = undefined) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error(`${path} -> ${response.status}`);
  }
  return response.json();
}

function renderSnapshot(snapshot) {
  snapshotTrust.textContent = formatTrust(snapshot.trust);
  snapshotBody.innerHTML = snapshot.features
    .map(
      (feature) => `
      <tr>
        <td>${feature.indicator_label}</td>
        <td>${formatNumber(feature.value)}</td>
        <td>${feature.source_id}</td>
        <td>${feature.observed_at}</td>
      </tr>
    `,
    )
    .join("");
}

function renderCompare(compare) {
  compareTrust.textContent = formatTrust(compare.trust);
  compareBody.innerHTML = compare.deltas
    .map(
      (delta) => `
      <tr>
        <td>${delta.indicator_label}</td>
        <td>${formatNumber(delta.current_value)}</td>
        <td>${formatNumber(delta.prior_value)}</td>
        <td>${formatNumber(delta.delta)}</td>
        <td>${delta.direction}</td>
      </tr>
    `,
    )
    .join("");
}

function renderSignals(signals) {
  signalsTrust.textContent = formatTrust(signals.trust);
  signalsBody.innerHTML = signals.signals
    .map(
      (signal) => `
      <tr>
        <td>${signal.signal_id}</td>
        <td>${signal.signal_type}</td>
        <td>${signal.strength}</td>
        <td>${formatNumber(signal.score)}</td>
        <td>${signal.trend}</td>
      </tr>
    `,
    )
    .join("");
}

function renderExplanation(explanation) {
  explanationTrust.textContent = formatTrust(explanation.trust);
  explanationSummary.textContent = explanation.summary;
  explanationPoints.innerHTML = (explanation.rationale_points || [])
    .map((point) => `<li>${point}</li>`)
    .join("");
}

async function loadSnapshot() {
  latestSnapshot = await getJson("/api/snapshots/latest?country=US");
  renderSnapshot(latestSnapshot);
}

async function loadCompare() {
  if (!latestSnapshot) {
    await loadSnapshot();
  }
  const priorFeatures = latestSnapshot.features.map((feature) => ({
    indicator_type: feature.indicator_type,
    value: Number(feature.value) * 0.98,
  }));

  const compare = await getJson("/api/snapshots/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      country: "US",
      prior_snapshot_label: "synthetic-prior",
      prior_features: priorFeatures,
    }),
  });
  renderCompare(compare);
}

async function loadSignals() {
  latestSignals = await getJson("/api/signals/latest?country=US");
  renderSignals(latestSignals);
}

async function loadExplanation() {
  if (!latestSignals) {
    await loadSignals();
  }
  const strongest = latestSignals.strongest_signal_id;
  const runId = latestSignals.run_id;
  if (!runId) {
    explanationTrust.textContent = "No experimental explanation available";
    explanationSummary.textContent = "";
    explanationPoints.innerHTML = "";
    return;
  }

  const explanationId = strongest ? `${runId}:${strongest}` : runId;
  try {
    const explanation = await getJson(`/api/explanations/${encodeURIComponent(explanationId)}`);
    renderExplanation(explanation);
  } catch {
    explanationTrust.textContent = "No experimental explanation found";
    explanationSummary.textContent = "";
    explanationPoints.innerHTML = "";
  }
}

async function loadAll() {
  try {
    await loadSnapshot();
    await loadCompare();
    await loadSignals();
    await loadExplanation();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    snapshotTrust.textContent = `Load error: ${message}`;
  }
}

document.getElementById("refresh-snapshot").addEventListener("click", () => {
  loadSnapshot();
});

document.getElementById("run-compare").addEventListener("click", () => {
  loadCompare();
});

document.getElementById("refresh-signals").addEventListener("click", async () => {
  await loadSignals();
  await loadExplanation();
});

loadAll();
