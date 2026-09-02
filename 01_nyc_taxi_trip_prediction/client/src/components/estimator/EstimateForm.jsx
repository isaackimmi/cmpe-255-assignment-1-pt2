import { Button, MenuItem, TextField } from "@mui/material";

const fields = [
  ["pickup_latitude", "Pickup latitude", "40.748"],
  ["pickup_longitude", "Pickup longitude", "-73.985"],
  ["dropoff_latitude", "Drop-off latitude", "40.765"],
  ["dropoff_longitude", "Drop-off longitude", "-73.955"],
];

export function EstimateForm({ onSubmit, submitting, error }) {
  const submit = (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(
      new FormData(event.currentTarget).entries(),
    );
    payload.passenger_count = Number(payload.passenger_count);
    onSubmit(payload);
  };
  return (
    <form className="panel form-grid" onSubmit={submit}>
      {fields.map(([name, label, value]) => (
        <TextField
          key={name}
          name={name}
          label={label}
          type="number"
          inputProps={{ step: "0.001" }}
          defaultValue={value}
          required
        />
      ))}
      <TextField
        className="wide"
        name="pickup_datetime"
        label="Pickup time"
        type="datetime-local"
        defaultValue="2016-03-18T17:30"
        InputLabelProps={{ shrink: true }}
        required
      />
      <TextField
        select
        name="passenger_count"
        label="Passengers"
        defaultValue="2"
      >
        {[1, 2, 3, 4].map((count) => (
          <MenuItem value={count} key={count}>
            {count}
          </MenuItem>
        ))}
      </TextField>
      <Button
        className="button primary wide"
        variant="contained"
        type="submit"
        disabled={submitting}
      >
        {submitting ? "Requesting estimate…" : "Request API estimate ↗"}
      </Button>
      <p className="error wide" role="alert">
        {error?.message}
      </p>
    </form>
  );
}
