export const MODULES = [
  { id: "overview", label: "Overview", index: null },
  { id: "cleaning", label: "Clean & validate", index: "01" },
  { id: "classification", label: "Classification", index: "02" },
  { id: "regression", label: "Regression", index: "03" },
  { id: "clustering", label: "Clustering", index: "04" },
];

export const MODULE_COPY = {
  overview: ["What the run actually measured.", "A compact view of the full pipeline and its evaluation boundaries."],
  cleaning: ["Trust the rows first.", "Validation, duplicates, missingness, and imputation are model inputs—not footnotes."],
  classification: ["Who is likely to renew?", "A fixed domain rule evaluated on a stratified holdout, with a majority-class baseline."],
  regression: ["Usage has a shape.", "A one-feature linear baseline predicts monthly usage from tenure on a seeded holdout."],
  clustering: ["Find the natural groups.", "Scaled usage and support-ticket behavior create descriptive customer segments without labels."],
};

export const MODULE_ROUTES = {
  cleaning: "/api/cleaning",
  classification: "/api/classification",
  regression: "/api/regression",
  clustering: "/api/clustering",
};
