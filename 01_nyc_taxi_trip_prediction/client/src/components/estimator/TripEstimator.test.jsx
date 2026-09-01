import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, taxiApi } from "../../services/api";
import { deferred } from "../../test/fixtures";
import { renderWithTheme } from "../../test/render";
import { TripEstimator } from "./TripEstimator";

afterEach(() => vi.restoreAllMocks());

describe("TripEstimator", () => {
  it("submits labeled fields, disables while pending, and renders the result", async () => {
    const result = deferred();
    const estimate = vi
      .spyOn(taxiApi, "estimate")
      .mockReturnValue(result.promise);
    const user = userEvent.setup();
    renderWithTheme(<TripEstimator />);
    expect(screen.getByLabelText(/Pickup latitude/)).toBeRequired();
    const submit = screen.getByRole("button", {
      name: "Request API estimate ↗",
    });
    await user.click(submit);
    expect(submit).toBeDisabled();
    expect(estimate).toHaveBeenCalledWith(
      expect.objectContaining({
        passenger_count: 2,
        pickup_datetime: "2016-03-18T17:30",
      }),
    );
    await act(async () =>
      result.resolve({
        estimated_duration_seconds: 300,
        distance_miles: 1.25,
        is_rush_hour: true,
        disclaimer: "Synthetic teaching estimate.",
      }),
    );
    expect(await screen.findByText("5:00")).toBeVisible();
    expect(screen.getByText("rush hour")).toBeVisible();
  });

  it("renders estimator errors without infrastructure policy", async () => {
    vi.spyOn(taxiApi, "estimate").mockRejectedValue(
      new ApiError("coordinates_outside_service_area", 422),
    );
    const user = userEvent.setup();
    renderWithTheme(<TripEstimator />);
    await user.click(
      screen.getByRole("button", { name: "Request API estimate ↗" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "coordinates_outside_service_area",
    );
    expect(screen.getByRole("alert")).not.toHaveTextContent("port 8001");
  });
});
