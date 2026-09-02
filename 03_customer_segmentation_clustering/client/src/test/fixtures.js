export const point = (id, cluster, overrides = {}) => ({
  customer_id: id,
  cluster,
  annual_income_k: 50 + cluster,
  spend_score: 60 + cluster,
  purchase_frequency: 4,
  avg_order_value: 70,
  pca_x: cluster,
  pca_y: cluster + 1,
  centroid_distance: 0.4,
  assignment_margin: 1.2,
  assignment_confidence: 0.8,
  uncertainty_label: "clear",
  ...overrides,
});

export const profiles = [0, 1].map((cluster) => ({ cluster, count: 1, name: `Segment ${cluster}`, guidance: "Hypothesis", means: { annual_income_k: 50, spend_score: 60, purchase_frequency: 4, avg_order_value: 70 } }));
