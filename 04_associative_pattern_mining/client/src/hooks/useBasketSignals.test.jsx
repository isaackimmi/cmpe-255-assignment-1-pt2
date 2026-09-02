import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/api", () => ({
  basketApi: {
    getSummary: vi.fn(),
    getItemsets: vi.fn(),
    getRules: vi.fn(),
    getTransactions: vi.fn(),
    getContext: vi.fn(),
  },
}));

import { basketApi } from "../services/api";
import { useBasketSignals } from "./useBasketSignals";

const summary = { transactions: 24, transaction_count: 24, items: 6, frequent_itemsets: 18, effective_support_count: 6, effective_support: 0.25 };

describe("useBasketSignals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    basketApi.getSummary.mockResolvedValue(summary);
    basketApi.getItemsets.mockResolvedValue({ rows: [{ label: "bread", support: 0.79, count: 19 }] });
    basketApi.getRules.mockResolvedValue({ rows: [{ label: "jam → butter", lift: 1.85 }] });
    basketApi.getTransactions.mockResolvedValue({ rows: [{ transaction_id: "T001", items: ["bread", "milk"] }] });
    basketApi.getContext.mockResolvedValue({ item: "bread", basket_count: 1, candidates: [] });
  });

  it("loads invariant transactions once and scopes sort and size requests", async () => {
    const { result } = renderHook(() => useBasketSignals());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(basketApi.getTransactions).toHaveBeenCalledTimes(1);

    act(() => result.current.setFilter("size", "2"));
    await waitFor(() => expect(basketApi.getItemsets).toHaveBeenCalledTimes(2));
    expect(basketApi.getSummary).toHaveBeenCalledTimes(1);
    expect(basketApi.getRules).toHaveBeenCalledTimes(1);
    expect(basketApi.getTransactions).toHaveBeenCalledTimes(1);

    act(() => result.current.setFilter("sort", "confidence"));
    await waitFor(() => expect(basketApi.getRules).toHaveBeenCalledTimes(2));
    expect(basketApi.getSummary).toHaveBeenCalledTimes(1);
    expect(basketApi.getTransactions).toHaveBeenCalledTimes(1);
  });

  it("debounces repeated threshold previews into one applied request", async () => {
    const { result } = renderHook(() => useBasketSignals());
    await waitFor(() => expect(result.current.loading).toBe(false));
    act(() => {
      result.current.setFilter("support", 0.3);
      result.current.setFilter("support", 0.35);
      result.current.setFilter("support", 0.4);
    });
    expect(basketApi.getSummary).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(basketApi.getSummary).toHaveBeenCalledTimes(2), { timeout: 700 });
    expect(basketApi.getRules).toHaveBeenCalledTimes(2);
    expect(basketApi.getItemsets).toHaveBeenCalledTimes(2);
    expect(basketApi.getTransactions).toHaveBeenCalledTimes(1);
  });

  it("recovers context independently without poisoning dashboard status", async () => {
    basketApi.getContext.mockRejectedValueOnce(new Error("context unavailable")).mockResolvedValueOnce({ item: "bread", basket_count: 1, candidates: [] });
    const { result } = renderHook(() => useBasketSignals());
    await waitFor(() => expect(result.current.contextError?.message).toBe("context unavailable"));
    expect(result.current.dashboardError).toBeNull();
    act(() => result.current.retryContext());
    await waitFor(() => expect(result.current.contextError).toBeNull());
    expect(result.current.status.tone).not.toBe("error");
  });
});
