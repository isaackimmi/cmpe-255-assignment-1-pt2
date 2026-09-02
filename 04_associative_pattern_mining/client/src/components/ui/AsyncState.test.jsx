import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { AsyncState } from "./AsyncState";

it("renders diagnostic detail near the failed section and retries", () => {
  const retry = vi.fn();
  render(<AsyncState error={new Error("API is offline")} onRetry={retry} title="Unable to load rules" />);
  expect(screen.getByRole("alert")).toHaveTextContent("API is offline");
  fireEvent.click(screen.getByRole("button", { name: "Retry" }));
  expect(retry).toHaveBeenCalledOnce();
});
