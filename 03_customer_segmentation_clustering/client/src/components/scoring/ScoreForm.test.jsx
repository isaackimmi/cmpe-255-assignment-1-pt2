import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { ScoreForm } from "./ScoreForm";

test("mirrors FastAPI numeric bounds and blocks invalid submission", () => {
  render(<ScoreForm values={{ annual_income_k: 14, spend_score: 100, purchase_frequency: 0.1, avg_order_value: 4 }} onChange={vi.fn()} onSubmit={vi.fn()} loading={false} />);
  expect(screen.getByRole("spinbutton", { name: /Annual income/ })).toHaveAttribute("min", "15");
  expect(screen.getByRole("spinbutton", { name: /Spend score/ })).toHaveAttribute("max", "99");
  expect(screen.getByRole("spinbutton", { name: /Purchase frequency/ })).toHaveAttribute("min", "0.2");
  expect(screen.getByRole("spinbutton", { name: /Average order value/ })).toHaveAttribute("min", "5");
  expect(screen.getByRole("button", { name: "Score observation" })).toBeDisabled();
});
