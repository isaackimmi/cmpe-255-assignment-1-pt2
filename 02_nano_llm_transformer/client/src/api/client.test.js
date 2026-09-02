import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, modelApi } from "./client";

describe("modelApi", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));

  it("maps UI generation fields to the FastAPI request schema", async () => {
    fetch.mockResolvedValue({ ok: true, json: async () => ({ generated: "ok" }) });
    const controller = new AbortController();
    await modelApi.generate({ prompt: "hello", maxNewTokens: 7, temperature: 0.4, signal: controller.signal });
    expect(fetch).toHaveBeenCalledWith("/api/generate", expect.objectContaining({
      method: "POST",
      signal: controller.signal,
      body: JSON.stringify({ prompt: "hello", max_new_tokens: 7, temperature: 0.4 }),
    }));
  });

  it("preserves structured API errors", async () => {
    fetch.mockResolvedValue({ ok: false, status: 503, json: async () => ({ error: { message: "artifact missing" } }) });
    await expect(modelApi.metrics()).rejects.toEqual(expect.objectContaining({
      name: "ApiError",
      message: "artifact missing",
      status: 503,
    }));
    await expect(modelApi.metrics()).rejects.toBeInstanceOf(ApiError);
  });
});
