import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithTheme } from "./test/render";
import { App } from "./App";
import { modelApi } from "./api/client";

vi.mock("./api/client", () => ({
  modelApi: {
    metrics: vi.fn(),
    behavior: vi.fn(),
    generate: vi.fn(),
    probabilities: vi.fn(),
  },
}));

const metrics = {
  backend: "stdlib_char_ngram",
  seed: 255,
  device: "cpu",
  test: { perplexity: 27.1, loss: 3.3, target_chars: 36 },
  split: { train_chars: 288, validation_chars: 36, test_chars: 36 },
  config: { order: 3 },
  vocabulary: ["<UNK>", "a"],
  corpus_sha256: "abcdef1234567890",
};

describe("App evidence states", () => {
  beforeEach(() => {
    modelApi.metrics.mockReset();
    modelApi.behavior.mockReset();
    modelApi.generate.mockReset();
    modelApi.probabilities.mockReset();
  });

  it("loads connected evidence and passes a basic axe scan", async () => {
    modelApi.metrics.mockResolvedValue(metrics);
    modelApi.behavior.mockResolvedValue({ order: 3 });
    const { container } = renderWithTheme(<App />);
    expect(screen.getByText("Loading model evidence…")).toBeInTheDocument();
    expect(await screen.findByText("● API connected")).toBeInTheDocument();
    expect(screen.getByText("27.1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate/i })).toBeEnabled();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("preserves metrics in a partial-evidence state", async () => {
    modelApi.metrics.mockResolvedValue(metrics);
    modelApi.behavior.mockRejectedValue(new Error("behavior unavailable"));
    renderWithTheme(<App />);
    expect(await screen.findByText("● API connected · partial evidence")).toBeInTheDocument();
    expect(screen.getByText("27.1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry evidence" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate/i })).toBeEnabled();
  });

  it("shows unavailable state and recovers through retry", async () => {
    modelApi.metrics.mockRejectedValueOnce(new Error("offline")).mockResolvedValue(metrics);
    modelApi.behavior.mockRejectedValueOnce(new Error("offline")).mockResolvedValue({ order: 3 });
    renderWithTheme(<App />);
    expect(await screen.findByText("● API unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate/i })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Retry evidence" }));
    await waitFor(() => expect(screen.getByText("● API connected")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /generate/i })).toBeEnabled();
  });
});
