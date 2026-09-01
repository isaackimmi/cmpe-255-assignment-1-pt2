import { percent } from "../../utils/format";

export function BarList({ rows, emptyMessage, labelFor, valueFor, countFor }) {
  if (!rows.length) return <p className="empty">{emptyMessage}</p>;
  return rows.map((row) => {
    const value = valueFor(row);
    return (
      <div className="bar-row" key={labelFor(row)}>
        <span title={labelFor(row)}>{labelFor(row)}</span>
        <div><i style={{ width: `${Math.max(2, value * 100)}%` }} /></div>
        <strong>{percent(value)}<small>{countFor(row)}</small></strong>
      </div>
    );
  });
}
