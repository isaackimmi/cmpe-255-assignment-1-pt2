import { useCallback, useEffect, useRef, useState } from "react";
import { segmentationApi } from "../api/segmentationApi";
import { validateDashboardPayload } from "../api/contracts";

export function useSegmentationData() {
  const [data, setData] = useState({ summary: null, profiles: [], points: [], validation: [] });
  const [status, setStatus] = useState("Connecting to FastAPI…");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const requestRef = useRef({ sequence: 0, controller: null });

  const refresh = useCallback(async () => {
    requestRef.current.controller?.abort();
    const controller = new AbortController();
    const sequence = requestRef.current.sequence + 1;
    requestRef.current = { sequence, controller };
    setLoading(true);
    setError(null);
    setStatus("Checking evidence manifest…");
    try {
      const evidence = await segmentationApi.evidenceStatus(controller.signal);
      if (!evidence.valid) throw new Error(`Evidence blocked: ${evidence.errors.join("; ")}`);
      const [summary, profiles, points, validation] = await Promise.all([
        segmentationApi.summary(controller.signal), segmentationApi.profiles(controller.signal), segmentationApi.points("all", controller.signal), segmentationApi.validation(controller.signal),
      ]);
      if (requestRef.current.sequence !== sequence) return;
      setData(validateDashboardPayload({ summary, profiles, points, validation }));
      setStatus("API connected · manifest verified");
    } catch (requestError) {
      if (requestError.name === "AbortError" || requestRef.current.sequence !== sequence) return;
      setError(requestError);
      setStatus("Evidence blocked");
    } finally {
      if (requestRef.current.sequence === sequence) setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    return () => requestRef.current.controller?.abort();
  }, [refresh]);
  return { ...data, status, error, loading, refresh };
}
