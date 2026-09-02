import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { ApiError, taxiApi } from "./services/api";
import {
  deferred,
  importanceFixture,
  metricsFixture,
  sliceFixture,
} from "./test/fixtures";
import { renderWithTheme } from "./test/render";

afterEach(() => vi.restoreAllMocks());

function mockSecondaryRequests() {
  vi.spyOn(taxiApi, "predictions").mockResolvedValue(sliceFixture());
  vi.spyOn(taxiApi, "estimate").mockResolvedValue({
    estimated_duration_seconds: 300,
    distance_miles: 1.2,
    is_rush_hour: false,
    disclaimer: "teaching estimate",
  });
}

describe("App evidence lifecycle", () => {
  it("renders loading state and then API-backed evidence", async () => {
    const experiment = deferred();
    const importance = deferred();
    vi.spyOn(taxiApi, "experiment").mockReturnValue(experiment.promise);
    vi.spyOn(taxiApi, "featureImportance").mockReturnValue(importance.promise);
    mockSecondaryRequests();
    renderWithTheme(<App />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Loading experiment evidence",
    );
    await act(async () => {
      experiment.resolve(metricsFixture);
      importance.resolve(importanceFixture);
    });
    expect(await screen.findAllByText("84.6 sec")).toHaveLength(2);
    expect(
      screen.getByRole("navigation", { name: "Primary navigation" }),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Estimator" })).toHaveAttribute(
      "href",
      "#estimate",
    );
  });

  it("shows a contextual network error and recovers through retry", async () => {
    const experiment = vi
      .spyOn(taxiApi, "experiment")
      .mockRejectedValueOnce(new ApiError("offline", 0))
      .mockResolvedValueOnce(metricsFixture);
    vi.spyOn(taxiApi, "featureImportance")
      .mockRejectedValueOnce(new ApiError("offline", 0))
      .mockResolvedValueOnce(importanceFixture);
    mockSecondaryRequests();
    const user = userEvent.setup();
    renderWithTheme(<App />);
    expect(
      await screen.findByText(/Cannot reach the analytics API/),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(
      await screen.findByText("The model earns its headline."),
    ).toBeVisible();
    expect(experiment).toHaveBeenCalledTimes(2);
  });
});
