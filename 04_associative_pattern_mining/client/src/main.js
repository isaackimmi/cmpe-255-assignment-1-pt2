import './styles.css';

const state = { support: 0.25, confidence: 0.60, count: 1, sort: 'lift', selectedItem: 'bread' };
let refreshToken = 0;
let activeController = null;
let contextToken = 0;
const $ = (selector) => document.querySelector(selector);
const api = async (path, signal) => {
  const response = await fetch(`/api/${path}`, { signal });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `API request failed: ${response.status}`);
  return response.json();
};
const qs = () => new URLSearchParams({ min_support: state.support, min_confidence: state.confidence, min_count: state.count, sort: state.sort });
const pct = (value) => `${(Number(value) * 100).toFixed(0)}%`;
const num = (value) => Number(value).toFixed(2);
const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

document.querySelector('#app').innerHTML = `
  <div class="app-shell">
    <header class="topbar"><a class="brand" href="#top"><span class="brand-mark">✦</span><span>basket<span class="muted">.</span>signals</span></a><span class="status" id="health"><i></i> connecting to API</span><span class="project-tag">CMPE 255 · PROJECT 04</span></header>
    <main id="top">
      <section class="hero"><div><p class="eyebrow">MARKET-BASKET INTELLIGENCE · CRISP-DM</p><h1>Find the products<br /><em>that travel together.</em></h1><p class="lede">An interactive evidence workbench for discovering itemsets, qualifying rules, and inspecting the baskets behind each signal.</p><a class="hero-link" href="#thresholds">Open the threshold lab ↓</a></div><div class="hero-art"><div class="orbit orbit-a"></div><div class="orbit orbit-b"></div><div class="node node-a">bread</div><div class="node node-b">milk</div><div class="node node-c">jam</div><div class="core">lift<strong>↗</strong></div></div></section>
      <section class="stats" id="stats"><article><span>TRANSACTIONS</span><strong id="stat-transactions">—</strong><small>source baskets</small></article><article><span>ITEM UNIVERSE</span><strong id="stat-items">—</strong><small id="stat-items-note">unique products</small></article><article><span>FREQUENT ITEMSETS</span><strong id="stat-itemsets">—</strong><small id="stat-itemsets-note">under current thresholds</small></article><article class="accent-card"><span>TOP LIFT</span><strong id="stat-lift">—</strong><small id="stat-lift-rule">waiting for rules</small></article></section>
      <section class="section" id="thresholds"><div class="section-head"><div><p class="eyebrow">01 / MODEL CONTROLS</p><h2>Turn the dials.<br /><em>Watch the evidence move.</em></h2></div><p class="section-note">The client queries FastAPI; the server reruns the same audited Apriori and rule-metric functions used by the Python experiment.</p></div><div class="control-panel"><div class="control"><label for="support">Minimum support <b id="support-value">25%</b></label><input id="support" type="range" min="5" max="100" step="5" value="25" /><small>prevalence across all baskets</small></div><div class="control"><label for="confidence">Minimum confidence <b id="confidence-value">60%</b></label><input id="confidence" type="range" min="5" max="100" step="5" value="60" /><small>share of antecedent baskets</small></div><div class="control"><label for="count">Minimum basket count <b id="count-value">1</b></label><input id="count" type="range" min="1" max="24" step="1" value="1" /><small>absolute denominator guardrail</small></div><div class="control-result"><strong id="effective-count">—</strong><span>effective count floor<br /><small id="effective-support">—</small></span></div></div></section>
      <section class="section chart-layout"><div><div class="section-head compact"><div><p class="eyebrow">02 / ITEMSETS</p><h2>Prevalence, made legible.</h2></div><label class="select-label">Pattern size <select id="size"><option value="">All sizes</option><option value="2">Pairs</option><option value="3">Triples</option></select></label></div><div class="chart card" id="itemset-chart"><p class="loading">Loading itemsets…</p></div><p class="source-note">Support = baskets containing the itemset / <span id="source-n">—</span> total baskets.</p></div><aside class="explain card"><p class="eyebrow">WHY IT MATTERS</p><h3>Support is the prevalence guardrail.</h3><p>A pattern can have impressive confidence simply because its consequent is popular. Start with support to make the denominator visible, then use confidence and lift to qualify the relationship.</p><div class="formula"><span>support</span><strong>count(itemset) / n baskets</strong></div><div class="formula"><span>lift</span><strong>confidence / support(consequent)</strong></div></aside></section>
      <section class="section" id="rules"><div class="section-head"><div><p class="eyebrow">03 / RULE BOARD</p><h2>Signals worth a closer look.</h2><p class="section-note">Exploratory, in-sample rules. Every card keeps the absolute support and antecedent denominator visible.</p></div><label class="select-label">Sort by <select id="sort"><option value="lift">Lift</option><option value="confidence">Confidence</option><option value="support">Support</option></select></label></div><div class="rule-grid" id="rules-grid"><p class="loading">Loading rules…</p></div></section>
      <section class="section explorer"><div class="section-head"><div><p class="eyebrow">04 / BASKET EXPLORER</p><h2>Put a basket under the lens.</h2></div><p class="section-note">Select a product to inspect its local co-occurrence context. This is not a rule; it is a conditional view for exploration.</p></div><div class="explorer-grid"><div class="card basket-card"><p class="eyebrow">SELECTED ITEM</p><select id="item-select"></select><div class="big-item" id="selected-item">bread</div><p><strong id="basket-count">—</strong> baskets contain this item.</p><div class="item-chips" id="item-chips"></div></div><div class="card context-card"><div class="card-title"><h3>What appears with it?</h3><span id="context-label">P(candidate | item)</span></div><div id="context-chart"><p class="loading">Select an item…</p></div></div></div></section>
      <section class="section method"><div class="section-head"><div><p class="eyebrow">05 / METHOD</p><h2>From baskets<br /><em>to decisions.</em></h2></div><p class="section-note">Apriori uses anti-monotonic pruning: if an itemset is not frequent, none of its supersets can be frequent. Rules are then derived and ranked by lift.</p></div><div class="method-grid"><div><span>01</span><strong>Understand</strong><p>Define a basket and business question.</p></div><div><span>02</span><strong>Prepare</strong><p>Trim tokens and collapse duplicates within each transaction.</p></div><div><span>03</span><strong>Mine</strong><p>Generate frequent itemsets with an explicit whole-basket threshold.</p></div><div><span>04</span><strong>Qualify</strong><p>Compare support, confidence, and lift before acting.</p></div></div></section>
    </main><footer><span>basket<span class="muted">.</span>signals</span><span>FastAPI + Vite · local evidence workbench</span><span>synthetic/local fixture · no production claims</span></footer>
  </div>`;

function renderStats(summary) {
  $('#stat-transactions').textContent = summary.transactions;
  $('#stat-items').textContent = summary.items;
  $('#stat-items-note').textContent = 'unique products in source';
  $('#stat-itemsets').textContent = summary.frequent_itemsets;
  $('#stat-itemsets-note').textContent = `${summary.effective_support_count}/${summary.transactions} basket floor`;
  $('#stat-lift').textContent = summary.rules ? 'ready' : '—';
  $('#stat-lift-rule').textContent = `${summary.rules} qualifying rules`;
  $('#effective-count').textContent = summary.effective_support_count;
  $('#effective-support').textContent = `${pct(summary.effective_support)} effective support`;
  $('#source-n').textContent = summary.transactions;
}

function renderItemsets(data) {
  const rows = data.rows.slice(0, 12);
  $('#itemset-chart').innerHTML = rows.length ? rows.map((row) => `<div class="bar-row"><span title="${esc(row.label)}">${esc(row.label)}</span><div><i style="width:${Math.max(2, row.support * 100)}%"></i></div><strong>${pct(row.support)}<small>${row.count}/${$('#stat-transactions').textContent}</small></strong></div>`).join('') : '<p class="empty">No itemsets clear this threshold. Lower support or count.</p>';
}

function renderRules(data) {
  const rows = data.rows.slice(0, 12);
  $('#rules-grid').innerHTML = rows.length ? rows.map((row, index) => `<article class="rule-card"><span class="rank">${String(index + 1).padStart(2, '0')} · exploratory rule</span><h3>${esc(row.label)}</h3><div class="rule-metrics"><div><span>Support</span><strong>${pct(row.support)}</strong><small>${Math.round(row.support_count)}/${$('#stat-transactions').textContent} baskets</small></div><div><span>Confidence</span><strong>${pct(row.confidence)}</strong><small>antecedent conditional</small></div><div><span>Lift</span><strong>${num(row.lift)}×</strong><small>vs independence</small></div></div></article>`).join('') : '<p class="empty">No rules meet the active thresholds.</p>';
  const top = data.rows[0]; if (top) { $('#stat-lift').textContent = `${num(top.lift)}×`; $('#stat-lift-rule').textContent = top.label; }
}

function renderContext(data) {
  $('#selected-item').textContent = data.item;
  $('#basket-count').textContent = data.basket_count;
  $('#context-chart').innerHTML = data.candidates.length ? data.candidates.slice(0, 8).map((row) => `<div class="bar-row"><span>${esc(row.item)}</span><div><i style="width:${Math.max(3, row.conditional_probability * 100)}%"></i></div><strong>${pct(row.conditional_probability)}<small>${row.count}/${data.basket_count}</small></strong></div>`).join('') : '<p class="empty">No co-occurring items.</p>';
}

async function refresh() {
  const token = ++refreshToken;
  activeController?.abort();
  activeController = new AbortController();
  const { signal } = activeController;
  $('#support-value').textContent = pct(state.support); $('#confidence-value').textContent = pct(state.confidence); $('#count-value').textContent = state.count;
  const query = qs();
  try { const [summary, itemsets, rules, tx] = await Promise.all([api(`summary?${query}`, signal), api(`itemsets?${query}`, signal), api(`rules?${query}`, signal), api('transactions', signal)]); if (token !== refreshToken) return; renderStats(summary); renderItemsets(itemsets); renderRules(rules); if (!$('#item-select').options.length) { const items = [...new Set(tx.rows.flatMap((row) => row.items))].sort(); $('#item-select').innerHTML = items.map((item) => `<option>${esc(item)}</option>`).join(''); $('#item-select').value = state.selectedItem; } await loadContext(signal, token); if (token === refreshToken) $('#health').innerHTML = '<i></i> API connected · artifacts live'; } catch (error) { if (error.name === 'AbortError' || token !== refreshToken) return; $('#health').innerHTML = `<i class="bad"></i> ${esc(error.message)}`; document.querySelectorAll('.loading').forEach((el) => { el.textContent = 'API unavailable — start FastAPI on port 8004.'; }); }
}
async function loadContext(signal = activeController?.signal, parentToken = refreshToken) { const token = ++contextToken; try { const data = await api(`context?item=${encodeURIComponent(state.selectedItem)}`, signal); if (parentToken === refreshToken && token === contextToken) renderContext(data); } catch (error) { if (error.name !== 'AbortError' && parentToken === refreshToken) $('#context-chart').innerHTML = `<p class="empty">${esc(error.message)}</p>`; } }
$('#support').addEventListener('input', (event) => { state.support = Number(event.target.value) / 100; refresh(); });
$('#confidence').addEventListener('input', (event) => { state.confidence = Number(event.target.value) / 100; refresh(); });
$('#count').addEventListener('input', (event) => { state.count = Number(event.target.value); refresh(); });
$('#sort').addEventListener('change', (event) => { state.sort = event.target.value; refresh(); });
$('#size').addEventListener('change', (event) => api(`itemsets?${qs()}&size=${event.target.value}`).then(renderItemsets).catch(() => {}));
$('#item-select').addEventListener('change', (event) => { state.selectedItem = event.target.value; loadContext(); });
refresh();
