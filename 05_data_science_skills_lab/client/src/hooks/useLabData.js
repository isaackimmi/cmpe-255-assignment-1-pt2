import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { labApi } from "../api/labApi";
import { MODULE_ROUTES } from "../constants/modules";

export const initialFilters = { plan: "all", renewal: "all", cluster: "all" };
const isAbort = (error) => error?.name === "AbortError";

export function useLabData() {
  const [summary, setSummary] = useState(null);
  const [module, setModule] = useState("overview");
  const [moduleData, setModuleData] = useState(null);
  const [filters, setFilters] = useState(initialFilters);
  const filtersRef = useRef(initialFilters);
  const [rowsResult, setRowsResult] = useState({ count: 0, rows: [], filters: initialFilters });
  const [pending, setPending] = useState({ summary: true, module: false, rows: true });
  const [errors, setErrors] = useState({ summary: null, module: null, rows: null });
  const controllers = useRef({ summary: null, module: null, rows: null });
  const requestIds = useRef({ summary: 0, module: 0, rows: 0 });

  const setRequestState = useCallback((key, value) => setPending((current) => ({ ...current, [key]: value })), []);
  const setRequestError = useCallback((key, value) => setErrors((current) => ({ ...current, [key]: value })), []);

  const loadRows = useCallback(async (nextFilters) => {
    controllers.current.rows?.abort();
    const controller = new AbortController();
    controllers.current.rows = controller;
    const requestId = ++requestIds.current.rows;
    setRequestState("rows", true);
    setRequestError("rows", null);
    try {
      const result = await labApi.getRows(nextFilters, { signal: controller.signal });
      if (requestIds.current.rows === requestId) setRowsResult(result);
    } catch (error) {
      if (!isAbort(error) && requestIds.current.rows === requestId) setRequestError("rows", error);
    } finally {
      if (requestIds.current.rows === requestId) setRequestState("rows", false);
    }
  }, [setRequestError, setRequestState]);

  const loadSummary = useCallback(async () => {
    controllers.current.summary?.abort();
    const controller = new AbortController();
    controllers.current.summary = controller;
    const requestId = ++requestIds.current.summary;
    setRequestState("summary", true);
    setRequestError("summary", null);
    try {
      const data = await labApi.getSummary({ signal: controller.signal });
      if (requestIds.current.summary !== requestId) return;
      setSummary(data);
      setModuleData(null);
      await loadRows(filtersRef.current);
    } catch (error) {
      if (!isAbort(error) && requestIds.current.summary === requestId) setRequestError("summary", error);
    } finally {
      if (requestIds.current.summary === requestId) setRequestState("summary", false);
    }
  }, [loadRows, setRequestError, setRequestState]);

  useEffect(() => {
    const activeControllers = controllers.current;
    loadSummary();
    return () => Object.values(activeControllers).forEach((controller) => controller?.abort());
  }, [loadSummary]);

  const selectModule = useCallback(async (nextModule) => {
    setModule(nextModule);
    controllers.current.module?.abort();
    const requestId = ++requestIds.current.module;
    setRequestError("module", null);
    if (nextModule === "overview") {
      setModuleData(null);
      setRequestState("module", false);
      return;
    }
    const controller = new AbortController();
    controllers.current.module = controller;
    setRequestState("module", true);
    try {
      const result = await labApi.getModule(nextModule, MODULE_ROUTES[nextModule], { signal: controller.signal });
      if (requestIds.current.module === requestId) setModuleData(result);
    } catch (error) {
      if (!isAbort(error) && requestIds.current.module === requestId) setRequestError("module", error);
    } finally {
      if (requestIds.current.module === requestId) setRequestState("module", false);
    }
  }, [setRequestError, setRequestState]);

  const updateFilter = useCallback((name, value) => {
    const nextFilters = { ...filtersRef.current, [name]: value };
    filtersRef.current = nextFilters;
    setFilters(nextFilters);
    loadRows(nextFilters);
  }, [loadRows]);

  const metrics = useMemo(() => {
    if (!summary) return null;
    const merged = { ...summary.metrics };
    if (module === "cleaning" && moduleData) merged.data_quality = moduleData;
    if (module === "classification" && moduleData) merged.classification = moduleData;
    if (module === "regression" && moduleData) merged.regression = moduleData.metrics;
    if (module === "clustering" && moduleData) merged.clustering = moduleData.metrics;
    return merged;
  }, [summary, module, moduleData]);

  const error = errors.summary || errors.module || errors.rows;
  const loading = pending.summary || pending.module || pending.rows;
  return { summary, metrics, module, moduleData, filters, rowsResult, pending, errors, loading, error, selectModule, updateFilter, retry: loadSummary };
}
