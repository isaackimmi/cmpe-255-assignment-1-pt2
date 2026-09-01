import { useState } from "react";
import { Alert, Card } from "@mui/material";
import { SectionHeading } from "../common/SectionHeading";
import { ScoreForm } from "./ScoreForm";
import { useScoreObservation } from "../../hooks/useScoreObservation";

const DEFAULTS = { annual_income_k: 72, spend_score: 78, purchase_frequency: 7, avg_order_value: 68 };

export function ScoringWorkbench() {
  const [values, setValues] = useState(DEFAULTS);
  const { result, error, loading, score } = useScoreObservation();
  const update = (field, value) => setValues((current) => ({ ...current, [field]: value }));
  const submit = (event) => { event.preventDefault(); score(values); };
  return <Card component="section" className="panel scoring"><SectionHeading eyebrow="NEW-CUSTOMER SCORING" title="Apply the selected geometry." description="This refits the canonical deterministic teaching model, then returns distances and assignment margin. It is not a business outcome prediction." /><ScoreForm values={values} onChange={update} onSubmit={submit} loading={loading} />{error && <Alert severity="error" sx={{ mt: 2 }}>{error.message}</Alert>}{result && <Alert severity="success" sx={{ mt: 2 }}>Assigned to segment {result.cluster}; nearest distance {result.nearest_distance}, margin {result.assignment_margin}. {result.note}.</Alert>}</Card>;
}
