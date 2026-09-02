import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";

const controls = [
  ["plan", "Plan", [["all", "All plans"], ["basic", "basic"], ["pro", "pro"], ["enterprise", "enterprise"]]],
  ["renewal", "Renewal", [["all", "All outcomes"], ["1", "Renewed"], ["0", "Not renewed"]]],
  ["cluster", "Cluster", [["all", "All groups"], ["0", "Cluster 0"], ["1", "Cluster 1"]]],
];

/** @param {{filters: {plan: string, renewal: string, cluster: string}, onChange: (name: string, value: string) => void, disabled: boolean}} props */
export function ExplorerFilters({ filters, onChange, disabled }) {
  return <div className="filters">{controls.map(([name, label, options]) => <FormControl key={name} size="small" disabled={disabled}>
    <InputLabel id={`${name}-label`}>{label}</InputLabel>
    <Select labelId={`${name}-label`} id={`${name}-filter`} value={filters[name]} label={label} onChange={(event) => onChange(name, event.target.value)}>
      {options.map(([value, text]) => <MenuItem key={value} value={value}>{text}</MenuItem>)}
    </Select>
  </FormControl>)}</div>;
}
