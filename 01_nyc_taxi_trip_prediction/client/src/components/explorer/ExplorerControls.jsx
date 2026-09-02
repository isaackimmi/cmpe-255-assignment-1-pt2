import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";

const slices = [
  ["all", "All rows"],
  ["rush", "Rush hour"],
  ["off_peak", "Off-peak"],
  ["short", "Short route"],
  ["long", "Long route"],
  ["weekend", "Weekend"],
  ["weekday", "Weekday"],
];

export function ExplorerControls({
  slice,
  population,
  onSliceChange,
  onPopulationChange,
}) {
  return (
    <div className="toolbar panel">
      <FormControl fullWidth size="small">
        <InputLabel id="population-label">Population</InputLabel>
        <Select
          labelId="population-label"
          label="Population"
          value={population}
          onChange={(event) => onPopulationChange(event.target.value)}
        >
          <MenuItem value="primary">All eligible holdout</MenuItem>
          <MenuItem value="robust">
            Train-threshold inliers · sensitivity
          </MenuItem>
        </Select>
      </FormControl>
      <FormControl fullWidth size="small">
        <InputLabel id="slice-label">Slice</InputLabel>
        <Select
          labelId="slice-label"
          label="Slice"
          value={slice}
          onChange={(event) => onSliceChange(event.target.value)}
        >
          {slices.map(([value, label]) => (
            <MenuItem value={value} key={value}>
              {label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </div>
  );
}
