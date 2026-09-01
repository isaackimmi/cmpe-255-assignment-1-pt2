import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";

export function SelectField({ id, label, value, onChange, options, disabled = false, size = "small" }) {
  return (
    <FormControl size={size} disabled={disabled} sx={{ minWidth: 135 }}>
      <InputLabel id={`${id}-label`}>{label}</InputLabel>
      <Select labelId={`${id}-label`} id={id} label={label} value={value} onChange={onChange}>
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
