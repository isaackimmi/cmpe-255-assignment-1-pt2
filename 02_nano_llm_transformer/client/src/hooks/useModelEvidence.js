import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { modelApi } from "../api/client";

export function useModelEvidence() {
  const [metrics, setMetrics] = useState(null);
  const [behavior, setBehavior] = useState(null);
  const [replay, setReplay] = useState(null);
  const [metricsState, setMetricsState] = useState("loading");
  const [behaviorState, setBehaviorState] = useState("loading");
  const [requestState, setRequestState] = useState("ready");
  const [loadError, setLoadError] = useState("");
  const [requestError, setRequestError] = useState("");
  const evidenceAbortRef = useRef(null);
  const generationAbortRef = useRef(null);
  const generationIdRef = useRef(0);

  const retryEvidence = useCallback(async () => {
    evidenceAbortRef.current?.abort();
    const controller = new AbortController();
    evidenceAbortRef.current = controller;
    setMetricsState("loading");
    setBehaviorState("loading");
    setLoadError("");
    const [metricsResult, behaviorResult] = await Promise.allSettled([
      modelApi.metrics({ signal: controller.signal }),
      modelApi.behavior({ signal: controller.signal }),
    ]);
    if (controller.signal.aborted) return;
    if (metricsResult.status === "fulfilled") {
      setMetrics(metricsResult.value);
      setMetricsState("success");
    } else {
      setMetrics(null);
      setMetricsState("error");
    }
    if (behaviorResult.status === "fulfilled") {
      setBehavior(behaviorResult.value);
      setBehaviorState("success");
    } else {
      setBehavior(null);
      setBehaviorState("error");
    }
    if (metricsResult.status === "rejected" || behaviorResult.status === "rejected") {
      const missing = [metricsResult, behaviorResult]
        .map((result, index) => result.status === "rejected" ? ["metrics", "behavior"][index] : null)
        .filter(Boolean)
        .join(" and ");
      setLoadError(`Unable to load ${missing} evidence. You can retry without reloading the page.`);
    }
  }, []);

  useEffect(() => {
    retryEvidence();
    return () => {
      evidenceAbortRef.current?.abort();
      generationAbortRef.current?.abort();
    };
  }, [retryEvidence]);

  const status = useMemo(() => {
    if (metricsState === "loading" || behaviorState === "loading") return "connecting";
    if (metricsState === "error") return "unavailable";
    if (behaviorState === "error") return "partial";
    return "connected";
  }, [behaviorState, metricsState]);

  const generate = useCallback(async ({ prompt, maxNewTokens, temperature }) => {
    generationAbortRef.current?.abort();
    const controller = new AbortController();
    generationAbortRef.current = controller;
    const generationId = ++generationIdRef.current;
    setRequestState("requesting");
    setRequestError("");
    try {
      const nextReplay = await modelApi.generate({ prompt, maxNewTokens, temperature, signal: controller.signal });
      if (generationId !== generationIdRef.current) return;
      const order = Number(nextReplay.context_order || behavior?.order || metrics?.config?.order || 0);
      const probabilityPayload = await modelApi.probabilities(prompt.slice(-order), { signal: controller.signal });
      if (generationId !== generationIdRef.current) return;
      const trace = (nextReplay.trace || []).map((step, index) => (
        index === 0 ? { ...step, candidates: probabilityPayload.candidates } : step
      ));
      setReplay({ ...nextReplay, trace });
      setRequestState("complete");
    } catch (error) {
      if (error.name === "AbortError" || generationId !== generationIdRef.current) return;
      setRequestState("error");
      setRequestError(error.message);
      throw error;
    }
  }, [behavior, metrics]);

  return {
    metrics,
    behavior,
    replay,
    status,
    canGenerate: status === "connected" || status === "partial",
    requestState,
    loadError,
    requestError,
    retryEvidence,
    generate,
  };
}
