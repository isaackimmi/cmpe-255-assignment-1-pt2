import { useCallback, useEffect, useMemo, useState } from "react";
import { basketApi } from "../services/api";

const INITIAL_FILTERS = { support: 0.25, confidence: 0.6, count: 1, sort: "lift", size: "" };
const THRESHOLD_DEBOUNCE_MS = 250;

function useRequest(effect, dependencies) {
  useEffect(() => {
    const controller = new AbortController();
    effect(controller.signal);
    return () => controller.abort();
    // The caller supplies stable primitive dependencies for each request surface.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
}

export function useBasketSignals() {
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState(INITIAL_FILTERS);
  const [summary, setSummary] = useState(null);
  const [itemsets, setItemsets] = useState([]);
  const [rules, setRules] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [selectedItem, setSelectedItem] = useState("bread");
  const [context, setContext] = useState(null);
  const [dashboardPending, setDashboardPending] = useState(0);
  const [contextLoading, setContextLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState(null);
  const [contextError, setContextError] = useState(null);
  const [dashboardRetryToken, setDashboardRetryToken] = useState(0);
  const [contextRetryToken, setContextRetryToken] = useState(0);

  const setFilter = useCallback((name, value) => {
    setFilters((current) => ({ ...current, [name]: value }));
    if (name === "sort" || name === "size") {
      setAppliedFilters((current) => ({ ...current, [name]: value }));
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setAppliedFilters((current) => ({
        ...current,
        support: filters.support,
        confidence: filters.confidence,
        count: filters.count,
      }));
    }, THRESHOLD_DEBOUNCE_MS);
    return () => window.clearTimeout(timeout);
  }, [filters.support, filters.confidence, filters.count]);

  const beginDashboardRequest = useCallback(() => {
    setDashboardPending((count) => count + 1);
    setDashboardError(null);
  }, []);
  const finishDashboardRequest = useCallback(() => setDashboardPending((count) => Math.max(0, count - 1)), []);
  const failDashboardRequest = useCallback((error) => {
    if (error.name !== "AbortError") setDashboardError(error);
  }, []);

  useRequest((signal) => {
    beginDashboardRequest();
    basketApi.getTransactions(signal)
      .then((payload) => setTransactions(payload.rows))
      .catch(failDashboardRequest)
      .finally(finishDashboardRequest);
  }, [dashboardRetryToken]);

  useRequest((signal) => {
    beginDashboardRequest();
    basketApi.getSummary(appliedFilters, signal)
      .then(setSummary)
      .catch(failDashboardRequest)
      .finally(finishDashboardRequest);
  }, [appliedFilters.support, appliedFilters.confidence, appliedFilters.count, dashboardRetryToken]);

  useRequest((signal) => {
    beginDashboardRequest();
    basketApi.getRules(appliedFilters, signal)
      .then((payload) => setRules(payload.rows))
      .catch(failDashboardRequest)
      .finally(finishDashboardRequest);
  }, [appliedFilters.support, appliedFilters.confidence, appliedFilters.count, appliedFilters.sort, dashboardRetryToken]);

  useRequest((signal) => {
    beginDashboardRequest();
    basketApi.getItemsets(appliedFilters, signal)
      .then((payload) => setItemsets(payload.rows))
      .catch(failDashboardRequest)
      .finally(finishDashboardRequest);
  }, [appliedFilters.support, appliedFilters.count, appliedFilters.size, dashboardRetryToken]);

  useRequest((signal) => {
    setContextLoading(true);
    setContextError(null);
    basketApi.getContext(selectedItem, signal)
      .then((payload) => {
        setContext(payload);
        setContextError(null);
      })
      .catch((error) => {
        if (error.name !== "AbortError") setContextError(error);
      })
      .finally(() => { if (!signal.aborted) setContextLoading(false); });
  }, [selectedItem, contextRetryToken]);

  const items = useMemo(() => [...new Set(transactions.flatMap((row) => row.items))].sort(), [transactions]);
  const loading = dashboardPending > 0;
  const status = dashboardError
    ? { tone: "error", label: "Dashboard unavailable" }
    : loading
      ? { tone: "loading", label: "Loading evidence" }
      : { tone: "success", label: "API connected · artifacts live" };

  return {
    filters,
    setFilter,
    summary,
    itemsets,
    rules,
    items,
    selectedItem,
    setSelectedItem,
    context,
    loading,
    contextLoading,
    dashboardError,
    contextError,
    retryDashboard: () => setDashboardRetryToken((token) => token + 1),
    retryContext: () => setContextRetryToken((token) => token + 1),
    status,
  };
}
