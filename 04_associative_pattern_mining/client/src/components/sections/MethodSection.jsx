import { SectionHeader } from "../ui/SectionHeader";

const STEPS = [
  ["01", "Understand", "Define a basket and business question."],
  ["02", "Prepare", "Trim tokens and collapse duplicates within each transaction."],
  ["03", "Mine", "Generate frequent itemsets with an explicit whole-basket threshold."],
  ["04", "Qualify", "Compare support, confidence, and lift before acting."],
];

export function MethodSection() {
  return (
    <section className="section method">
      <SectionHeader
        eyebrow="05 / METHOD"
        title={<>From baskets<br /><em>to decisions.</em></>}
        note="Apriori uses anti-monotonic pruning: if an itemset is not frequent, none of its supersets can be frequent. Rules are then derived and ranked by lift."
      />
      <div className="method-grid">
        {STEPS.map(([number, title, body]) => <div key={number}><span>{number}</span><strong>{title}</strong><p>{body}</p></div>)}
      </div>
    </section>
  );
}
