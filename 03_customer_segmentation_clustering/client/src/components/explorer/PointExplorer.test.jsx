import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { PointExplorer } from "./PointExplorer";
import { point, profiles } from "../../test/fixtures";

const points = [point("C001", 0), point("C002", 1)];
const baseProps = { points, profiles, projection: "raw", onProjectionChange: vi.fn(), xFeature: "spend_score", onXChange: vi.fn(), yFeature: "annual_income_k", onYChange: vi.fn() };

test("keeps the inspector selection inside the active segment", async () => {
  const onSelect = vi.fn();
  const { rerender } = render(<PointExplorer {...baseProps} cluster="all" onClusterChange={vi.fn()} selectedId="C001" onSelect={onSelect} />);
  expect(screen.getByRole("heading", { name: /C001 Segment 0/i })).toBeInTheDocument();
  rerender(<PointExplorer {...baseProps} cluster="1" onClusterChange={vi.fn()} selectedId="C001" onSelect={onSelect} />);
  expect(screen.queryByRole("heading", { name: /C001/i })).not.toBeInTheDocument();
  await waitFor(() => expect(onSelect).toHaveBeenCalledWith("C002"));
});

test("uses one roving tab stop and arrow-key point navigation", async () => {
  const user = userEvent.setup(); const onSelect = vi.fn();
  render(<PointExplorer {...baseProps} cluster="all" onClusterChange={vi.fn()} selectedId="C001" onSelect={onSelect} />);
  const options = screen.getAllByRole("option");
  expect(options.filter((option) => option.tabIndex === 0)).toHaveLength(1);
  options[0].focus();
  await user.keyboard("{ArrowRight}");
  expect(onSelect).toHaveBeenCalledWith("C002");
  expect(screen.getByText(/Accessible point data \(2 customers\)/)).toBeInTheDocument();
});
