/* Browser-side companion to analysis.py. transactions.js is generated from
   data/transactions.csv so this page remains offline without a second data
   source to edit by hand. */
const transactions = window.TRANSACTION_ROWS.map(({ id, items }) => ({ id, items: new Set(items) }));

const itemUniverse = [...new Set(transactions.flatMap(({ items }) => [...items]))].sort();
const initialSupport = 0.25;
const initialConfidence = 0.60;
const initialSupportCount = Math.ceil(initialSupport * transactions.length - 1e-10);
const state = { showAllRules: false, selectedBasketId: 'T001', ruleSort: 'lift' };

const $ = (selector) => document.querySelector(selector);
const pct = (value) => `${Math.round(value * 100)}%`;
const metric = (value) => value.toFixed(2);
const setKey = (items) => [...items].sort().join('|');
const setLabel = (items) => [...items].sort().join(' + ');
const countFor = (itemset) => transactions.filter(({ items }) => [...itemset].every((item) => items.has(item))).length;

function getSupport(itemset) {
  return countFor(itemset) / transactions.length;
}

function combinations(items, size) {
  if (size === 0) return [[]];
  if (size > items.length) return [];
  const output = [];
  items.forEach((item, index) => {
    combinations(items.slice(index + 1), size - 1).forEach((tail) => output.push([item, ...tail]));
  });
  return output;
}

function allSubsets(items) {
  return Array.from({ length: items.length - 1 }, (_, index) => index + 1)
    .flatMap((size) => combinations(items, size).map((subset) => new Set(subset)));
}

function minimumSupportCount(minSupport, minimumCount) {
  return Math.max(Math.ceil(minSupport * transactions.length - 1e-10), minimumCount);
}

function apriori(minSupport, minimumCount = 1) {
  const thresholdCount = minimumSupportCount(minSupport, minimumCount);
  const frequent = new Map();
  let candidates = itemUniverse.map((item) => new Set([item]));
  let size = 1;
  while (candidates.length) {
    const current = candidates.filter((candidate) => countFor(candidate) >= thresholdCount);
    current.forEach((itemset) => frequent.set(setKey(itemset), {
      items: itemset,
      support: getSupport(itemset),
      count: countFor(itemset),
    }));
    size += 1;
    const next = new Map();
    combinations(itemUniverse, size).forEach((items) => {
      const candidate = new Set(items);
      if (combinations(items, size - 1).every((subset) => frequent.has(setKey(new Set(subset))))) {
        next.set(setKey(candidate), candidate);
      }
    });
    candidates = [...next.values()];
  }
  return frequent;
}

function associationRules(frequent, minConfidence) {
  const rules = [];
  frequent.forEach(({ items, support: itemsetSupport, count: supportCount }) => {
    if (items.size < 2) return;
    const sortedItems = [...items].sort();
    allSubsets(sortedItems).forEach((antecedent) => {
      const consequent = new Set(sortedItems.filter((item) => !antecedent.has(item)));
      const antecedentCount = countFor(antecedent);
      const consequentCount = countFor(consequent);
      const confidence = supportCount / antecedentCount;
      const lift = confidence / (consequentCount / transactions.length);
      if (confidence >= minConfidence) rules.push({
        antecedent,
        consequent,
        support: itemsetSupport,
        supportCount,
        antecedentCount,
        consequentCount,
        confidence,
        lift,
      });
    });
  });
  return sortRules(rules, 'lift');
}

function sortRules(rules, sortBy = state.ruleSort) {
  const score = (rule) => sortBy === 'support'
    ? [-rule.support, -rule.confidence, -rule.lift]
    : sortBy === 'confidence'
      ? [-rule.confidence, -rule.lift, -rule.support]
      : [-rule.lift, -rule.confidence, -rule.support];
  return [...rules].sort((a, b) => {
    const scoresA = score(a);
    const scoresB = score(b);
    for (let index = 0; index < scoresA.length; index += 1) {
      if (scoresA[index] !== scoresB[index]) return scoresA[index] - scoresB[index];
    }
    return setLabel(a.antecedent).localeCompare(setLabel(b.antecedent))
      || setLabel(a.consequent).localeCompare(setLabel(b.consequent));
  });
}

function currentMining() {
  const support = Number($('#support-slider').value) / 100;
  const confidence = Number($('#confidence-slider').value) / 100;
  const minimumCount = Number($('#support-count-slider').value);
  const thresholdCount = minimumSupportCount(support, minimumCount);
  const effectiveSupport = thresholdCount / transactions.length;
  const frequent = apriori(support, minimumCount);
  const rules = associationRules(frequent, confidence);
  return { confidence, effectiveSupport, frequent, minimumCount, rules, support, thresholdCount };
}

function renderStats(frequent, rules, threshold) {
  $('#stat-transactions').textContent = transactions.length;
  $('#stat-items').textContent = itemUniverse.length;
  $('#stat-items-foot').textContent = itemUniverse.join(' · ');
  $('#stat-itemsets').textContent = frequent.size;
  $('#stat-support').textContent = `${pct(threshold.effectiveSupport)} · at least ${threshold.thresholdCount}/${transactions.length}`;
  $('#threshold-count').textContent = frequent.size;
  $('#threshold-count-foot').textContent = `${threshold.thresholdCount}/${transactions.length} basket floor`;
  $('#chart-n').textContent = transactions.length;
  $('#effective-support').textContent = `${pct(threshold.effectiveSupport)} (${threshold.thresholdCount}/${transactions.length})`;
  $('#confidence-value').textContent = pct(threshold.confidence);
  $('#support-count-value').textContent = `${threshold.minimumCount}/${transactions.length}`;
  const bestRule = rules[0];
  $('#stat-lift').textContent = bestRule ? `${metric(bestRule.lift)}×` : '—';
  $('#stat-lift-rule').textContent = bestRule ? `${setLabel(bestRule.antecedent)} → ${setLabel(bestRule.consequent)}` : 'No qualifying rule';
}

function renderChart(frequent) {
  const sizeFilter = $('#itemset-size').value;
  const filtered = [...frequent.values()].filter(({ items }) => sizeFilter === 'all' || (sizeFilter === '2+' ? items.size >= 2 : items.size === Number(sizeFilter)));
  const top = filtered.sort((a, b) => b.support - a.support || b.items.size - a.items.size || setLabel(a.items).localeCompare(setLabel(b.items))).slice(0, 10);
  $('#chart-filter-note').textContent = `${top.length} of ${filtered.length} itemsets shown · ${sizeFilter === 'all' ? 'all sizes' : sizeFilter === '2+' ? 'pairs and larger' : `${sizeFilter}-item patterns`}`;
  $('#support-chart').innerHTML = top.length ? top.map(({ items, support, count }) => `
    <div class="chart-row"><span class="chart-label" title="${setLabel(items)}">${setLabel(items)}</span><span class="bar-track"><span class="bar-fill" style="width:${support * 100}%"></span></span><span class="chart-value">${pct(support)}<small>${count}/${transactions.length}</small></span></div>`).join('') : '<p class="empty-state">No itemsets clear this threshold.</p>';
}

function renderRules(rules) {
  const sortedRules = sortRules(rules);
  const visible = state.showAllRules ? sortedRules : sortedRules.slice(0, 8);
  $('#rule-count').textContent = sortedRules.length ? `Showing ${visible.length} of ${sortedRules.length} rules` : '0 qualifying rules';
  $('#show-all-rules').textContent = state.showAllRules ? 'Show top 8' : `Show all ${sortedRules.length} rules`;
  $('#show-all-rules').hidden = sortedRules.length <= 8;
  $('#rules-grid').innerHTML = visible.length ? visible.map((rule, index) => `
    <article class="rule-card"><span class="rule-rank">${String(index + 1).padStart(2, '0')} · exploratory / in-sample</span><div class="rule-arrow"><span class="rule-side">${setLabel(rule.antecedent)}</span><br><span aria-hidden="true">→</span> <span class="rule-side right">${setLabel(rule.consequent)}</span></div><div class="rule-metrics"><div class="rule-metric"><span>Support</span><strong>${pct(rule.support)}<small>${rule.supportCount}/${transactions.length} baskets</small></strong></div><div class="rule-metric"><span>Confidence</span><strong>${pct(rule.confidence)}<small>${rule.supportCount}/${rule.antecedentCount} antecedent baskets</small></strong></div><div class="rule-metric"><span>Lift</span><strong>${metric(rule.lift)}×<small>vs ${rule.consequentCount}/${transactions.length}</small></strong></div></div></article>`).join('') : `<div class="card empty-state">No rules meet ${pct(thresholdConfidence())} confidence at this prevalence threshold. Lower confidence or the prevalence floor to reveal more candidates.</div>`;
}

function thresholdConfidence() {
  return Number($('#confidence-slider').value) / 100;
}

function renderTriggeredRules(rules, basket) {
  const triggered = sortRules(rules.filter((rule) => [...rule.antecedent].every((item) => basket.items.has(item))));
  $('#basket-rule-count').textContent = `${triggered.length} triggered`;
  $('#triggered-rules').innerHTML = triggered.length ? triggered.map((rule) => {
    const alreadyPresent = [...rule.consequent].every((item) => basket.items.has(item));
    return `<div class="triggered-rule"><div class="triggered-rule-line"><span>${setLabel(rule.antecedent)}</span><span class="trigger-arrow" aria-hidden="true">→</span><strong>${setLabel(rule.consequent)}</strong></div><div class="triggered-rule-meta"><span>${alreadyPresent ? 'already in basket' : 'candidate consequent'}</span><span>${pct(rule.confidence)} confidence · ${metric(rule.lift)}× lift</span><span>${rule.supportCount}/${rule.antecedentCount} antecedent baskets</span></div></div>`;
  }).join('') : '<p class="empty-state">No qualifying rule has an antecedent contained in this basket. Adjust the active thresholds or inspect another transaction.</p>';
}

function renderBasket(id) {
  const basketIndex = transactions.findIndex((transaction) => transaction.id === id);
  const basket = transactions[basketIndex];
  if (!basket) return;
  state.selectedBasketId = id;
  const threshold = currentMining();
  const matched = [...threshold.frequent.values()].filter(({ items }) => items.size > 1 && [...items].every((item) => basket.items.has(item))).length;
  $('#basket-title').textContent = `Basket ${basket.id}`;
  $('#basket-items').innerHTML = [...basket.items].map((item) => `<span class="item-chip">${item}</span>`).join('');
  $('#basket-size').textContent = basket.items.size;
  $('#basket-match').textContent = `${matched} frequent pattern${matched === 1 ? '' : 's'}`;
  $('#basket-id-label').textContent = basket.id;
  $('#basket-row').textContent = String(basketIndex + 1).padStart(2, '0');
  renderTriggeredRules(threshold.rules, basket);

  const withBasketItem = transactions.filter(({ items }) => [...basket.items].some((basketItem) => items.has(basketItem)));
  const context = itemUniverse.filter((item) => !basket.items.has(item)).map((item) => {
    const candidateCount = withBasketItem.filter(({ items }) => items.has(item)).length;
    return { item, candidateCount, denominator: withBasketItem.length, share: withBasketItem.length ? candidateCount / withBasketItem.length : 0 };
  }).sort((a, b) => b.share - a.share || a.item.localeCompare(b.item));
  $('#context-list').innerHTML = context.map(({ item, candidateCount, denominator, share }) => `<div class="context-row"><span class="context-product">${item}</span><span class="context-track"><span class="context-fill" style="width:${share * 100}%"></span></span><span class="context-percent">${pct(share)}<small>${candidateCount}/${denominator}</small></span></div>`).join('');
}

function renderThreshold() {
  const threshold = currentMining();
  $('#support-value').textContent = pct(threshold.support);
  $('#support-slider').style.background = `linear-gradient(to right, var(--coral) 0%, var(--coral) ${threshold.support * 100}%, #e4e9e8 ${threshold.support * 100}%, #e4e9e8 100%)`;
  $('#confidence-slider').style.background = `linear-gradient(to right, var(--coral) 0%, var(--coral) ${threshold.confidence * 100}%, #e4e9e8 ${threshold.confidence * 100}%, #e4e9e8 100%)`;
  $('#support-count-slider').style.background = `linear-gradient(to right, var(--coral) 0%, var(--coral) ${(threshold.minimumCount / transactions.length) * 100}%, #e4e9e8 ${(threshold.minimumCount / transactions.length) * 100}%, #e4e9e8 100%)`;
  renderStats(threshold.frequent, threshold.rules, threshold);
  renderChart(threshold.frequent);
  renderRules(threshold.rules);
  renderBasket(state.selectedBasketId);
}

function init() {
  $('#basket-select').innerHTML = transactions.map(({ id }, index) => `<option value="${id}">${id} · row ${String(index + 1).padStart(2, '0')}</option>`).join('');
  $('#support-slider').value = String(initialSupport * 100);
  $('#confidence-slider').value = String(initialConfidence * 100);
  $('#support-count-slider').value = String(initialSupportCount);
  $('#basket-select').addEventListener('change', (event) => renderBasket(event.target.value));
  $('#support-slider').addEventListener('input', renderThreshold);
  $('#confidence-slider').addEventListener('input', renderThreshold);
  $('#support-count-slider').addEventListener('input', renderThreshold);
  $('#itemset-size').addEventListener('change', () => renderChart(currentMining().frequent));
  $('#rule-sort').addEventListener('change', (event) => {
    state.ruleSort = event.target.value;
    renderRules(currentMining().rules);
    renderBasket(state.selectedBasketId);
  });
  $('#show-all-rules').addEventListener('click', () => {
    state.showAllRules = !state.showAllRules;
    renderRules(currentMining().rules);
  });
  renderThreshold();
}

if (typeof window !== 'undefined') {
  // A tiny public surface lets the offline parity test exercise the same
  // browser miner without needing a browser or a local server.
  window.BASKET_SIGNALS = { apriori, associationRules, countFor, getSupport };
}

if (typeof document !== 'undefined') init();
