import { act, renderHook, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { segmentationApi } from "../api/segmentationApi";
import { useSegmentationData } from "./useSegmentationData";
import { point } from "../test/fixtures";

vi.mock("../api/segmentationApi", () => ({ segmentationApi: { evidenceStatus: vi.fn(), summary: vi.fn(), profiles: vi.fn(), points: vi.fn(), validation: vi.fn() } }));

test("aborts an older evidence refresh so stale requests cannot win", async () => {
  const pending = [];
  segmentationApi.evidenceStatus.mockImplementation((signal) => new Promise((resolve) => pending.push({ resolve, signal })));
  segmentationApi.summary.mockResolvedValue({ selected_k: 2, features: ["annual_income_k", "spend_score", "purchase_frequency", "avg_order_value"], validation: { silhouette_mean: 0.5 }, fit_metrics: { silhouette: 0.6 } });
  segmentationApi.profiles.mockResolvedValue([{ cluster: 0, means: { annual_income_k: 50, spend_score: 60, purchase_frequency: 4, avg_order_value: 70 } }]);
  segmentationApi.points.mockResolvedValue([point("C001", 0)]);
  segmentationApi.validation.mockResolvedValue([]);
  const { result, unmount } = renderHook(() => useSegmentationData());
  await waitFor(() => expect(pending).toHaveLength(1));
  act(() => { result.current.refresh(); });
  await waitFor(() => expect(pending).toHaveLength(2));
  expect(pending[0].signal.aborted).toBe(true);
  await act(async () => { pending[1].resolve({ valid: true, errors: [] }); });
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.points[0].customer_id).toBe("C001");
  unmount();
  expect(pending[1].signal.aborted).toBe(true);
});
