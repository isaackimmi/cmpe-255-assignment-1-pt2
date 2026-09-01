import { act, renderHook, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { segmentationApi } from "../api/segmentationApi";
import { useScoreObservation } from "./useScoreObservation";

vi.mock("../api/segmentationApi", () => ({ segmentationApi: { score: vi.fn() } }));

test("keeps only the latest scoring response", async () => {
  const pending = [];
  segmentationApi.score.mockImplementation((values, signal) => new Promise((resolve) => pending.push({ values, signal, resolve })));
  const { result } = renderHook(() => useScoreObservation());
  act(() => { result.current.score({ annual_income_k: 50 }); result.current.score({ annual_income_k: 70 }); });
  await waitFor(() => expect(pending).toHaveLength(2));
  expect(pending[0].signal.aborted).toBe(true);
  await act(async () => { pending[1].resolve({ cluster: 2 }); });
  await waitFor(() => expect(result.current.result).toEqual({ cluster: 2 }));
});
