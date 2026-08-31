/* Browser-side companion to analysis.py. It intentionally embeds the checked-in
   CSV so index.html works offline when opened directly from the file system. */
const transactionCsv = `transaction_id,items
T001,"bread;milk;eggs"
T002,"bread;milk;butter"
T003,"bread;milk;eggs;butter"
T004,"bread;jam;butter"
T005,"milk;eggs;coffee"
T006,"bread;milk;eggs"
T007,"bread;milk;butter;coffee"
T008,"bread;jam;butter"
T009,"milk;eggs;coffee"
T010,"bread;milk;eggs;coffee"
T011,"bread;milk;butter"
T012,"bread;jam;butter;coffee"
T013,"milk;eggs"
T014,"bread;milk;eggs;butter"
T015,"bread;milk;coffee"
T016,"bread;jam;butter"
T017,"milk;eggs;coffee"
T018,"bread;milk;eggs"
T019,"bread;milk;butter;coffee"
T020,"bread;jam;butter;coffee"
T021,"milk;eggs;coffee"
T022,"bread;milk;eggs;butter"
T023,"bread;milk;coffee"
T024,"bread;jam;butter"`;

const transactions = transactionCsv.trim().split('\n').slice(1).map((line) => {
  const [id, itemText] = line.split(',"');
  return { id, items: new Set(itemText.replace(/"$/, '').split(';')) };
});

const itemUniverse = [...new Set(transactions.flatMap(({ items }) => [...items]))].sort();
const initialSupport = 0.25;
const minConfidence = 0.60;

const $ = (selector) => document.querySelector(selector);
const pct = (value) => `${Math.round(value * 100)}%`;
const metric = (value) => value.toFixed(2);
const setKey = (items) => [...items].sort().join('|');
const setLabel = (items) => [...items].sort().join(' + ');

function getSupport(itemset) {
  return transactions.filter(({ items }) => [...itemset].every((item) => items.has(item))).length / transactions.length;
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

function apriori(minSupport) {
  const frequent = new Map();
  let candidates = itemUniverse.map((item) => new Set([item]));
  let size = 1;
  while (candidates.length) {
    const current = candidates.filter((candidate) => getSupport(candidate) >= minSupport - 1e-10);
    current.forEach((itemset) => frequent.set(setKey(itemset), { items: itemset, support: getSupport(itemset) }));
    size += 1;
    const next = new Map();
    combinations(itemUniverse, size).forEach((items) => {
      const candidate = new Set(items);
      if (combinations(items, size - 1).every((subset) => frequent.has(setKey(new Set(subset))))) next.set(setKey(candidate), candidate);
    });
    candidates = [...next.values()];
  }
  return frequent;
}

function associationRules(frequent) {
  const rules = [];
  frequent.forEach(({ items, support: itemsetSupport }) => {
    if (items.size < 2) return;
    const sortedItems = [...items].sort();
    allSubsets(sortedItems).forEach((antecedent) => {
      const consequent = new Set(sortedItems.filter((item) => !antecedent.has(item)));
      const antecedentSupport = frequent.get(setKey(antecedent))?.support ?? getSupport(antecedent);
      const consequentSupport = frequent.get(setKey(consequent))?.support ?? getSupport(consequent);
      const confidence = itemsetSupport / antecedentSupport;
      const lift = confidence / consequentSupport;
      if (confidence >= minConfidence) rules.push({ antecedent, consequent, support: itemsetSupport, confidence, lift });
    });
  });
  return rules.sort((a, b) => b.lift - a.lift || b.confidence - a.confidence || setLabel(a.antecedent).localeCompare(setLabel(b.antecedent)));
}

function renderStats(frequent, rules, support) {
  $('#stat-transactions').textContent = transactions.length;
  $('#stat-items').textContent = itemUniverse.length;
  $('#stat-itemsets').textContent = frequent.size;
  $('#stat-support').textContent = pct(support);
  $('#threshold-count').textContent = frequent.size;
  $('#chart-n').textContent = transactions.length;
  const bestRule = rules[0];
  $('#stat-lift').textContent = bestRule ? `${metric(bestRule.lift)}×` : '—';
  $('#stat-lift-rule').textContent = bestRule ? `${setLabel(bestRule.antecedent)} → ${setLabel(bestRule.consequent)}` : 'No qualifying rule';
}

function renderChart(frequent) {
  const top = [...frequent.values()].sort((a, b) => b.support - a.support || setLabel(a.items).localeCompare(setLabel(b.items))).slice(0, 8);
  $('#support-chart').innerHTML = top.length ? top.map(({ items, support }) => `
    <div class="chart-row"><span class="chart-label" title="${setLabel(items)}">${setLabel(items)}</span><span class="bar-track"><span class="bar-fill" style="width:${support * 100}%"></span></span><span class="chart-value">${pct(support)}</span></div>`).join('') : '<p class="empty-state">No itemsets clear this threshold.</p>';
}

function renderRules(rules) {
  const visible = rules.slice(0, 8);
  $('#rule-count').textContent = `${visible.length} rule${visible.length === 1 ? '' : 's'} shown`;
  $('#rules-grid').innerHTML = visible.length ? visible.map((rule, index) => `
    <article class="rule-card"><span class="rule-rank">0${index + 1} / ${setLabel(rule.antecedent).length > 20 ? 'compound' : 'clear signal'}</span><div class="rule-arrow"><span class="rule-side">${setLabel(rule.antecedent)}</span><br><span aria-hidden="true">→</span> <span class="rule-side right">${setLabel(rule.consequent)}</span></div><div class="rule-metrics"><div class="rule-metric"><span>Support</span><strong>${pct(rule.support)}</strong></div><div class="rule-metric"><span>Confidence</span><strong>${pct(rule.confidence)}</strong></div><div class="rule-metric"><span>Lift</span><strong>${metric(rule.lift)}×</strong></div></div></article>`).join('') : '<div class="card empty-state">No rules meet 60% confidence at this support threshold. Lower the threshold to reveal more candidates.</div>';
}

function renderThreshold() {
  const support = Number($('#support-slider').value) / 100;
  const frequent = apriori(support);
  const rules = associationRules(frequent);
  $('#support-value').textContent = pct(support);
  $('#support-slider').style.background = `linear-gradient(to right, var(--coral) 0%, var(--coral) ${support * 100}%, #e4e9e8 ${support * 100}%, #e4e9e8 100%)`;
  renderStats(frequent, rules, support);
  renderChart(frequent);
  renderRules(rules);
}

function renderBasket(id) {
  const basketIndex = transactions.findIndex((transaction) => transaction.id === id);
  const basket = transactions[basketIndex];
  if (!basket) return;
  const frequent = apriori(Number($('#support-slider').value) / 100);
  const matched = [...frequent.values()].filter(({ items }) => items.size > 1 && [...items].every((item) => basket.items.has(item))).length;
  $('#basket-title').textContent = `Basket ${basket.id}`;
  $('#basket-items').innerHTML = [...basket.items].map((item) => `<span class="item-chip">${item}</span>`).join('');
  $('#basket-size').textContent = basket.items.size;
  $('#basket-match').textContent = `${matched} frequent pattern${matched === 1 ? '' : 's'}`;
  $('#basket-id-label').textContent = basket.id;
  $('#basket-row').textContent = String(basketIndex + 1).padStart(2, '0');

  const context = itemUniverse.filter((item) => !basket.items.has(item)).map((item) => {
    const withCandidate = transactions.filter(({ items }) => items.has(item));
    const coPickCount = withCandidate.filter(({ items }) => [...basket.items].some((basketItem) => items.has(basketItem))).length;
    return { item, share: withCandidate.length ? coPickCount / withCandidate.length : 0 };
  }).sort((a, b) => b.share - a.share);
  $('#context-list').innerHTML = context.map(({ item, share }) => `<div class="context-row"><span class="context-product">${item}</span><span class="context-track"><span class="context-fill" style="width:${share * 100}%"></span></span><span class="context-percent">${pct(share)}</span></div>`).join('');
}

function init() {
  $('#basket-select').innerHTML = transactions.map(({ id }, index) => `<option value="${id}">${id} · row ${String(index + 1).padStart(2, '0')}</option>`).join('');
  $('#basket-select').addEventListener('change', (event) => renderBasket(event.target.value));
  $('#support-slider').addEventListener('input', renderThreshold);
  renderThreshold();
  renderBasket('T001');
}

init();
