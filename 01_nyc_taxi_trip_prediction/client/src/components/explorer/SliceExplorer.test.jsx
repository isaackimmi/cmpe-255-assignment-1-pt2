import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { taxiApi } from "../../services/api";
import { deferred, sliceFixture } from "../../test/fixtures";
import { renderWithTheme } from "../../test/render";
import { SliceExplorer } from "./SliceExplorer";

afterEach(() => vi.restoreAllMocks());

describe("SliceExplorer", () => {
  it("sends selected slice and population and keeps the latest response", async () => {
    const first = deferred();
    const rush = deferred();
    const requests = [];
    vi.spyOn(taxiApi, "predictions").mockImplementation((options) => {
      requests.push(options);
      if (options.slice === "all") return first.promise;
      return rush.promise;
    });
    const user = userEvent.setup();
    renderWithTheme(<SliceExplorer enabled />);
    await user.click(screen.getByLabelText("Slice"));
    await user.click(await screen.findByRole("option", { name: "Rush hour" }));
    expect(requests[0].signal.aborted).toBe(true);
    await act(async () => rush.resolve(sliceFixture("rush", "primary", 3)));
    expect(
      await screen.findByRole("heading", { name: "rush · primary" }),
    ).toBeVisible();
    await act(async () => first.resolve(sliceFixture("all", "primary", 9)));
    expect(
      screen.getByRole("heading", { name: "rush · primary" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("heading", { name: "all · primary" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByLabelText("Population"));
    await user.click(
      await screen.findByRole("option", { name: /Train-threshold inliers/ }),
    );
    expect(taxiApi.predictions).toHaveBeenLastCalledWith(
      expect.objectContaining({ slice: "rush", population: "robust" }),
    );
  });

  it("renders a semantic prediction table and accessible residual summary", async () => {
    vi.spyOn(taxiApi, "predictions").mockResolvedValue(sliceFixture());
    renderWithTheme(<SliceExplorer enabled />);
    const table = await screen.findByRole("table", {
      name: /Actual and predicted trip durations/,
    });
    expect(
      within(table).getByRole("columnheader", { name: "Pickup" }),
    ).toBeVisible();
    expect(
      screen.getByRole("img", { name: "Absolute residual magnitude chart" }),
    ).toHaveAccessibleDescription(/Mean absolute residual/);
  });
});
