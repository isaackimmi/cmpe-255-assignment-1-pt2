import { Button, TextField } from "@mui/material";
import { fieldError, SCORING_FIELDS } from "../../constants/scoringFields";

export function ScoreForm({ values, onChange, onSubmit, loading }) {
  return (
    <form onSubmit={onSubmit} className="score-form">
      {Object.entries(SCORING_FIELDS).map(([field, contract]) => {
        const error = fieldError(field, values[field]);
        return <TextField key={field} label={contract.label} type="number" value={values[field]} onChange={(event) => onChange(field, Number(event.target.value))} inputProps={{ min: contract.min, max: contract.max, step: contract.step }} error={Boolean(error)} helperText={error || contract.helperText} required />;
      })}
      <Button type="submit" variant="contained" disabled={loading || Object.keys(SCORING_FIELDS).some((field) => fieldError(field, values[field]))}>{loading ? "Scoring…" : "Score observation"}</Button>
    </form>
  );
}
