import { displayToken, percentage } from "../../utils/format";

export function ProbabilityList({ candidates = [] }) {
  if (!candidates.length) return <p className="empty">Generate a response to see normalized probabilities.</p>;
  return (
    <ul className="prob-list" aria-label="Next-character probability distribution">
      {candidates.map((item, index) => (
        <li className="prob-row" key={`${item.token}-${index}`}>
          <b>{displayToken(item.token)}</b>
          <span className="prob-meter" role="meter" aria-label={`${displayToken(item.token)} probability`} aria-valuemin="0" aria-valuemax="100" aria-valuenow={Number(item.probability) * 100}>
            <span style={{ width: `${Math.max(2, Number(item.probability) * 100)}%` }} />
          </span>
          <strong>{percentage(item.probability)}</strong>
        </li>
      ))}
    </ul>
  );
}
