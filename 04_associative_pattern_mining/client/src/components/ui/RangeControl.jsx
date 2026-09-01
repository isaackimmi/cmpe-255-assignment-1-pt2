import * as Slider from "@radix-ui/react-slider";

export function RangeControl({ id, label, value, displayValue, min, max, step, help, onChange }) {
  return (
    <div className="control">
      <label id={`${id}-label`} htmlFor={id}>{label} <b>{displayValue}</b></label>
      <Slider.Root
        id={id}
        className="radix-slider"
        min={min}
        max={max}
        step={step}
        value={[value]}
        onValueChange={([next]) => onChange(next)}
        aria-labelledby={`${id}-label`}
      >
        <Slider.Track className="radix-slider-track"><Slider.Range className="radix-slider-range" /></Slider.Track>
        <Slider.Thumb className="radix-slider-thumb" />
      </Slider.Root>
      <small>{help}</small>
    </div>
  );
}
