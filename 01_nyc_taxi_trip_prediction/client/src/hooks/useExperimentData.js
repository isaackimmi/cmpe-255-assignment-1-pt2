import { useCallback, useEffect, useRef, useState } from "react";
import { taxiApi } from "../services/api";

export function useExperimentData() {
  const [data, setData] = useState({ metrics: null, importance: [] });
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);
  const controllerRef = useRef(null);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    const requestId = ++requestIdRef.current;
    controllerRef.current = controller;
    setStatus("loading");
    setError(null);
    try {
      const [metrics, importance] = await Promise.all([
        taxiApi.experiment({ signal: controller.signal }),
        taxiApi.featureImportance({ signal: controller.signal }),
      ]);
      if (controller.signal.aborted || requestId !== requestIdRef.current)
        return;
      setData({ metrics, importance });
      setStatus("success");
    } catch (requestError) {
      if (
        requestError?.name === "AbortError" ||
        requestId !== requestIdRef.current
      )
        return;
      setError(requestError);
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    reload();
    return () => {
      requestIdRef.current += 1;
      controllerRef.current?.abort();
    };
  }, [reload]);

  return { ...data, status, error, reload };
}
