export const SCORING_FIELDS = {
  annual_income_k: { label: "Annual income ($k)", min: 15, step: 0.1, helperText: "At least 15" },
  spend_score: { label: "Spend score", min: 1, max: 99, step: 1, helperText: "Between 1 and 99" },
  purchase_frequency: { label: "Purchase frequency", min: 0.2, step: 0.1, helperText: "At least 0.2" },
  avg_order_value: { label: "Average order value", min: 5, step: 0.1, helperText: "At least 5" },
};

export function fieldError(field, value) {
  const contract = SCORING_FIELDS[field];
  if (!Number.isFinite(value)) return "Enter a number";
  if (value < contract.min) return `Must be at least ${contract.min}`;
  if (contract.max != null && value > contract.max) return `Must be at most ${contract.max}`;
  return "";
}
