"""Reproducible market-basket mining with Apriori and association rules."""
from __future__ import annotations

import csv
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "transactions.csv"

REQUIRED_COLUMNS = ("transaction_id", "items")


def load_transaction_rows(path: Path = DATA_PATH) -> list[dict[str, object]]:
    """Load and validate transaction rows from the checked-in CSV.

    Product names are trimmed and duplicate mentions within a basket are
    intentionally collapsed into a set. Empty fields, duplicate IDs, missing
    columns, and extra columns are rejected so the denominator is explicit.
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise ValueError(f"CSV must contain exactly these columns: {', '.join(REQUIRED_COLUMNS)}")

        rows: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            if row.get(None) is not None:
                raise ValueError(f"row {line_number} has extra CSV fields")
            transaction_id = (row.get("transaction_id") or "").strip()
            if not transaction_id:
                raise ValueError(f"row {line_number} has an empty transaction_id")
            if transaction_id in seen_ids:
                raise ValueError(f"row {line_number} repeats transaction_id {transaction_id!r}")

            item_text = row.get("items")
            if item_text is None or not item_text.strip():
                raise ValueError(f"row {line_number} has no products")
            raw_items = item_text.split(";")
            if any(not item.strip() for item in raw_items):
                raise ValueError(f"row {line_number} contains an empty product token")
            items = frozenset(item.strip() for item in raw_items)
            if not items:
                raise ValueError(f"row {line_number} has no products after trimming")

            seen_ids.add(transaction_id)
            rows.append({"transaction_id": transaction_id, "items": items})
    if not rows:
        raise ValueError("CSV must contain at least one transaction")
    return rows


def load_transactions(path: Path = DATA_PATH) -> list[frozenset[str]]:
    return [row["items"] for row in load_transaction_rows(path)]  # type: ignore[return-value]


def _validate_transactions(transactions: Iterable[frozenset[str]]) -> list[frozenset[str]]:
    normalized = [frozenset(transaction) for transaction in transactions]
    if not normalized:
        raise ValueError("transactions must be non-empty")
    if any(not transaction for transaction in normalized):
        raise ValueError("transactions cannot contain an empty basket")
    return normalized


def _validate_probability(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 1:
        raise ValueError(f"{name} must be in (0, 1]")


def support(itemset: frozenset[str], transactions: list[frozenset[str]]) -> float:
    if not itemset:
        raise ValueError("itemset must be non-empty")
    normalized = _validate_transactions(transactions)
    return sum(itemset <= tx for tx in normalized) / len(normalized)

def apriori(transactions: list[frozenset[str]], min_support: float = 0.25) -> dict[frozenset[str], float]:
    """Return all frequent itemsets using level-wise Apriori pruning."""
    normalized = _validate_transactions(transactions)
    _validate_probability(min_support, "min_support")
    threshold = min_support * len(normalized)
    counts = Counter(item for tx in normalized for item in tx)
    current = {frozenset([item]) for item, count in counts.items() if count >= threshold}
    frequent = {itemset: support(itemset, normalized) for itemset in current}
    k = 2
    while current:
        prior = sorted(current, key=lambda s: tuple(sorted(s)))
        candidates = {frozenset(a | b) for a, b in combinations(prior, 2) if len(a | b) == k}
        candidates = {c for c in candidates if all(frozenset(subset) in current for subset in combinations(c, k - 1))}
        current = {c for c in candidates if support(c, normalized) >= min_support}
        frequent.update({itemset: support(itemset, normalized) for itemset in current})
        k += 1
    return frequent

def association_rules(frequent: dict[frozenset[str], float], min_confidence: float = 0.60) -> list[dict]:
    """Generate non-empty antecedent/consequent rules with confidence and lift."""
    _validate_probability(min_confidence, "min_confidence")
    for itemset, value in frequent.items():
        if not itemset:
            raise ValueError("frequent must map non-empty itemsets to supports in (0, 1]")
        _validate_probability(value, "support")
    rules = []
    for itemset, itemset_support in frequent.items():
        if len(itemset) < 2:
            continue
        for size in range(1, len(itemset)):
            for antecedent_tuple in combinations(sorted(itemset), size):
                antecedent = frozenset(antecedent_tuple)
                consequent = itemset - antecedent
                if antecedent not in frequent or consequent not in frequent:
                    raise ValueError("frequent is missing a required subset support")
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
