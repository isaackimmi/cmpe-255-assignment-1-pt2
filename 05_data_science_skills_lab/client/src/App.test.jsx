import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import App from "./App";
import { useLabData } from "./hooks/useLabData";
import { metrics, rowsResponse, summaryResponse } from "./test/fixtures";

vi.mock("./hooks/useLabData", () => ({ useLabData: vi.fn() }));

const base = {
  summary: summaryResponse, metrics, module: "overview", moduleData: null,
  filters: rowsResponse.filters, rowsResult: rowsResponse,
  pending: { summary: false, module: false, rows: false }, errors: { summary: null, module: null, rows: null },
  loading: false, error: null, selectModule: vi.fn(), updateFilter: vi.fn(), retry: vi.fn(),
};

describe("App behavior", () => {
  it("composes navigation, evidence, and the honest global filter result", () => {
    useLabData.mockReturnValue(base);
    render(<App/>);
    expect(screen.getByText("What the run actually measured.")).toBeInTheDocument();
    expect(screen.getByText(/filter the row evidence only/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /classification/i }));
    expect(base.selectModule).toHaveBeenCalledWith("classification");
  });

  it("shows a retry action for request errors", () => {
    const retry = vi.fn();
    useLabData.mockReturnValue({ ...base, error: new Error("broken evidence"), errors: { summary: new Error("broken evidence"), module: null, rows: null }, retry });
    render(<App/>);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(retry).toHaveBeenCalled();
  });
});
