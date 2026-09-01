import * as Select from "@radix-ui/react-select";

export function SelectField({ label, value, options, onChange }) {
  return (
    <label className="select-label">
      <span>{label}</span>
      <Select.Root value={String(value)} onValueChange={onChange}>
        <Select.Trigger className="select-trigger" aria-label={label}>
          <Select.Value />
          <Select.Icon aria-hidden="true">⌄</Select.Icon>
        </Select.Trigger>
        <Select.Portal>
          <Select.Content className="select-content" position="popper" sideOffset={6}>
            <Select.Viewport>
              {options.map((option) => (
                <Select.Item className="select-item" value={String(option.value)} key={String(option.value)}>
                  <Select.ItemText>{option.label}</Select.ItemText>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </label>
  );
}
