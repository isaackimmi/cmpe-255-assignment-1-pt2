import { useEffect, useRef, useState } from "react";
import { taxiApi } from "../services/api";

export function usePredictionSlice(slice, population, enabled = true) {
  const [state, setState] = useState({
    data: null,
    loading: enabled,
    error: null,
  });
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setState({ data: null, loading: false, error: null });
      return undefined;
    }
    const controller = new AbortController();
    const requestId = ++requestIdRef.current;
    setState((current) => ({ ...current, loading: true, error: null }));
    taxiApi
      .predictions({ slice, population, signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setState({ data, loading: false, error: null });
        }
      })
      .catch((error) => {
        if (error.name !== "AbortError" && requestId === requestIdRef.current)
          setState({ data: null, loading: false, error });
      });
    return () => {
      controller.abort();
    };
  }, [enabled, population, slice]);

  return state;
}
