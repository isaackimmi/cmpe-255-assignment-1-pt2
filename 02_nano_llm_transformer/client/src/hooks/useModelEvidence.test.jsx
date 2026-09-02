import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { modelApi } from "../api/client";
import { useModelEvidence } from "./useModelEvidence";

vi.mock("../api/client", () => ({
  modelApi: { metrics: vi.fn(), behavior: vi.fn(), generate: vi.fn(), probabilities: vi.fn() },
}));

function Harness() {
  const evidence = useModelEvidence();
  return (
    <div>
      <span>{evidence.status}</span>
      <span data-testid="generated">{evidence.replay?.generated || "none"}</span>
      <button onClick={() => evidence.generate({ prompt: "first", maxNewTokens: 1, temperature: 0 })}>First</button>
      <button onClick={() => evidence.generate({ prompt: "second", maxNewTokens: 1, temperature: 0 })}>Second</button>
    </div>
  );
}

describe("useModelEvidence generation concurrency", () => {
  beforeEach(() => {
    modelApi.metrics.mockResolvedValue({ config: { order: 3 } });
    modelApi.behavior.mockResolvedValue({ order: 3 });
    modelApi.probabilities.mockResolvedValue({ candidates: [] });
  });

  it("aborts the previous generation and keeps the latest result", async () => {
    let firstSignal;
    modelApi.generate.mockImplementation(({ prompt, signal }) => {
      if (prompt === "second") return Promise.resolve({ generated: "second result", trace: [], context_order: 3 });
      firstSignal = signal;
      return new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError"))));
    });
    render(<Harness />);
    await screen.findByText("connected");
    await userEvent.click(screen.getByRole("button", { name: "First" }));
    await userEvent.click(screen.getByRole("button", { name: "Second" }));
    await waitFor(() => expect(screen.getByTestId("generated")).toHaveTextContent("second result"));
    expect(firstSignal.aborted).toBe(true);
  });
});
