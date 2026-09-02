import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { labApi } from "../api/labApi";
import { useLabData } from "./useLabData";
import { metrics, rowsResponse, summaryResponse } from "../test/fixtures";

vi.mock("../api/labApi", () => ({ labApi: { getSummary: vi.fn(), getRows: vi.fn(), getModule: vi.fn() } }));

const deferred = () => {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
};

beforeEach(() => {
  labApi.getSummary.mockResolvedValue(summaryResponse);
  labApi.getRows.mockResolvedValue(rowsResponse);
  labApi.getModule.mockReset();
});

describe("useLabData request ownership", () => {
  it("commits only the latest module response", async () => {
    const first = deferred();
    const second = deferred();
    labApi.getModule.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const { result } = renderHook(() => useLabData());
    await waitFor(() => expect(result.current.summary).toBeTruthy());
    act(() => { result.current.selectModule("cleaning"); result.current.selectModule("classification"); });
    await act(async () => second.resolve(metrics.classification));
    await waitFor(() => expect(result.current.moduleData).toEqual(metrics.classification));
    await act(async () => first.resolve(metrics.data_quality));
    expect(result.current.module).toBe("classification");
    expect(result.current.moduleData).toEqual(metrics.classification);
  });

  it("keeps the latest accumulated filters when responses resolve out of order", async () => {
    const first = deferred();
    const second = deferred();
    const { result } = renderHook(() => useLabData());
    await waitFor(() => expect(result.current.summary).toBeTruthy());
    labApi.getRows.mockReset().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    act(() => { result.current.updateFilter("plan", "pro"); result.current.updateFilter("renewal", "1"); });
    await act(async () => second.resolve({ ...rowsResponse, count: 7, filters: { plan: "pro", renewal: "1", cluster: "all" } }));
    await waitFor(() => expect(result.current.rowsResult.count).toBe(7));
    await act(async () => first.resolve({ ...rowsResponse, count: 2 }));
    expect(result.current.rowsResult.count).toBe(7);
    expect(labApi.getRows).toHaveBeenLastCalledWith({ plan: "pro", renewal: "1", cluster: "all" }, expect.any(Object));
  });
});
