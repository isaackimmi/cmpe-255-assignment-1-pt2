import { validateDashboardPayload } from "./contracts";
import { point } from "../test/fixtures";

const summary = { selected_k: 2, features: ["annual_income_k", "spend_score", "purchase_frequency", "avg_order_value"], validation: { silhouette_mean: 0.5 }, fit_metrics: { silhouette: 0.6 } };
const profiles = [{ cluster: 0, means: { annual_income_k: 50, spend_score: 60, purchase_frequency: 4, avg_order_value: 70 } }];

test("rejects malformed nested point evidence before rendering", () => {
  expect(() => validateDashboardPayload({ summary, profiles, points: [point("C001", 0, { assignment_margin: "not-a-number" })], validation: [] })).toThrow(/assignment_margin must be finite/);
});
