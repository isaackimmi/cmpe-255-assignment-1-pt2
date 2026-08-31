"""Reproducible market-basket mining with Apriori and association rules."""
from __future__ import annotations

import csv
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "transactions.csv"

def load_transactions(path: Path = DATA_PATH) -> list[frozenset[str]]:
    with path.open(newline="") as handle:
        return [frozenset(row["items"].split(";")) for row in csv.DictReader(handle)]

def support(itemset: frozenset[str], transactions: list[frozenset[str]]) -> float:
    return sum(itemset <= tx for tx in transactions) / len(transactions)

def apriori(transactions: list[frozenset[str]], min_support: float = 0.25) -> dict[frozenset[str], float]:
    """Return all frequent itemsets using level-wise Apriori pruning."""
    if not transactions or not 0 < min_support <= 1:
        raise ValueError("transactions must be non-empty and min_support must be in (0, 1]")
    threshold = min_support * len(transactions)
    counts = Counter(item for tx in transactions for item in tx)
    current = {frozenset([item]) for item, count in counts.items() if count >= threshold}
    frequent = {itemset: support(itemset, transactions) for itemset in current}
    k = 2
    while current:
        prior = sorted(current, key=lambda s: tuple(sorted(s)))
        candidates = {frozenset(a | b) for a, b in combinations(prior, 2) if len(a | b) == k}
        candidates = {c for c in candidates if all(frozenset(subset) in current for subset in combinations(c, k - 1))}
        current = {c for c in candidates if support(c, transactions) >= min_support}
        frequent.update({itemset: support(itemset, transactions) for itemset in current})
        k += 1
    return frequent

def association_rules(frequent: dict[frozenset[str], float], min_confidence: float = 0.60) -> list[dict]:
    """Generate non-empty antecedent/consequent rules with confidence and lift."""
    rules = []
    for itemset, itemset_support in frequent.items():
        if len(itemset) < 2:
            continue
        for size in range(1, len(itemset)):
            for antecedent_tuple in combinations(sorted(itemset), size):
                antecedent = frozenset(antecedent_tuple)
                consequent = itemset - antecedent
                confidence = itemset_support / frequent[antecedent]
                lift = confidence / frequent[consequent]
                if confidence >= min_confidence:
                    rules.append({"antecedent": antecedent, "consequent": consequent, "support": itemset_support, "confidence": confidence, "lift": lift})
    return sorted(rules, key=lambda r: (-r["lift"], -r["confidence"], sorted(r["antecedent"])))

def save_plot(frequent: dict[frozenset[str], float], output: Path = ROOT / "outputs" / "support_plot.svg") -> Path:
    """Write a dependency-free SVG bar chart of the ten most supported itemsets."""
    top = sorted(frequent.items(), key=lambda x: (-x[1], tuple(sorted(x[0]))))[:10]
    output.parent.mkdir(exist_ok=True)
    width, row_height, left = 900, 42, 260
    height = 80 + row_height * len(top)
    rows = []
    for i, (items, value) in enumerate(top):
        y = 50 + i * row_height
        label = " + ".join(sorted(items)).replace("&", "&amp;")
        rows.append(f'<text x="{left - 12}" y="{y + 18}" text-anchor="end" font-size="14">{label}</text>')
        rows.append(f'<rect x="{left}" y="{y}" width="{int(value * 560)}" height="24" fill="#34d399"/>')
        rows.append(f'<text x="{left + int(value * 560) + 8}" y="{y + 18}" font-size="13">{value:.3f}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
           '<rect width="100%" height="100%" fill="#0f172a"/><text x="30" y="28" fill="white" font-size="18" font-family="sans-serif">Frequent itemsets — support</text>'
           + ''.join(row.replace('font-size="', 'fill="white" font-family="sans-serif" font-size="') for row in rows) + '</svg>')
    output.write_text(svg)
    return output

def main() -> None:
    transactions = load_transactions()
    frequent = apriori(transactions, min_support=0.25)
    rules = association_rules(frequent, min_confidence=0.60)
    print(f"Transactions: {len(transactions)}")
    print(f"Frequent itemsets: {len(frequent)}")
    print("Top rules:")
    for rule in rules[:8]:
        left = ", ".join(sorted(rule["antecedent"]))
        right = ", ".join(sorted(rule["consequent"]))
        print(f"  {{{left}}} -> {{{right}}} | support={rule['support']:.3f} confidence={rule['confidence']:.3f} lift={rule['lift']:.3f}")
    print(f"Plot: {save_plot(frequent)}")

if __name__ == "__main__":
    main()
