import { BarList } from "../ui/BarList";

export function ItemsetList({ rows, transactionCount }) {
  return (
    <BarList
      rows={rows.slice(0, 12)}
      emptyMessage="No itemsets clear this threshold. Lower support or count."
      labelFor={(row) => row.label}
      valueFor={(row) => row.support}
      countFor={(row) => `${row.count}/${transactionCount}`}
    />
  );
}
