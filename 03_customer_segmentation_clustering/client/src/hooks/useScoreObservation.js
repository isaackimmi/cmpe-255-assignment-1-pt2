import { useCallback, useEffect, useRef, useState } from "react";
import { segmentationApi } from "../api/segmentationApi";

export function useScoreObservation() {
  const [state, setState] = useState({ result: null, error: null, loading: false });
  const requestRef = useRef({ sequence: 0, controller: null });

  const score = useCallback(async (values) => {
    requestRef.current.controller?.abort();
    const controller = new AbortController();
    const sequence = requestRef.current.sequence + 1;
    requestRef.current = { sequence, controller };
    setState({ result: null, error: null, loading: true });
    try {
      const result = await segmentationApi.score(values, controller.signal);
      if (requestRef.current.sequence === sequence) setState({ result, error: null, loading: false });
    } catch (error) {
      if (error.name !== "AbortError" && requestRef.current.sequence === sequence) setState({ result: null, error, loading: false });
    }
  }, []);

  useEffect(() => () => requestRef.current.controller?.abort(), []);
  return { ...state, score };
}
