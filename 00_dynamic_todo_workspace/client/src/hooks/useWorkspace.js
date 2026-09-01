import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { workspaceApi } from "../services/api";

export function useWorkspace() {
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const pendingRef = useRef("");
  const latestLoadRef = useRef(0);

  const loadWorkspace = useCallback(async (signal) => {
    const requestId = ++latestLoadRef.current;
    try {
      const nextWorkspace = await workspaceApi.getWorkspace({ signal });
      if (requestId === latestLoadRef.current && !signal?.aborted) {
        setWorkspace(nextWorkspace);
        setError(null);
      }
    } catch (requestError) {
      if (requestError.name !== "AbortError" && requestId === latestLoadRef.current) setError(requestError);
    } finally {
      if (requestId === latestLoadRef.current && !signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadWorkspace(controller.signal);
    return () => controller.abort();
  }, [loadWorkspace]);

  const mutate = useCallback(async (key, action) => {
    if (pendingRef.current) return { ok: false, reason: "busy" };
    pendingRef.current = key;
    setPending(key);
    setStatusMessage("Saving change…");
    try {
      const tasks = await action();
      if (tasks) setWorkspace((current) => ({ ...current, tasks }));
      setStatusMessage("Saved");
      return { ok: true };
    } catch (requestError) {
      setStatusMessage(`Could not save: ${requestError.message}`);
      return { ok: false, reason: "request", error: requestError };
    } finally {
      pendingRef.current = "";
      setPending("");
    }
  }, []);

  const createTask = useCallback(
    (task) => mutate("add", () => workspaceApi.createTask(task)),
    [mutate],
  );
  const toggleTask = useCallback(
    (taskId, done) => mutate(`toggle-${taskId}`, () => workspaceApi.updateTask(taskId, { done })),
    [mutate],
  );
  const deleteTask = useCallback(
    (taskId) => mutate(`delete-${taskId}`, () => workspaceApi.deleteTask(taskId)),
    [mutate],
  );
  const runAgentCheck = useCallback(
    () => mutate("agent", async () => {
      await workspaceApi.runAgentCheck();
      const refreshed = await workspaceApi.getWorkspace();
      setWorkspace(refreshed);
      return null;
    }),
    [mutate],
  );

  return useMemo(
    () => ({ workspace, loading, error, pending, statusMessage, busy: Boolean(pending), createTask, toggleTask, deleteTask, runAgentCheck }),
    [workspace, loading, error, pending, statusMessage, createTask, toggleTask, deleteTask, runAgentCheck],
  );
}
