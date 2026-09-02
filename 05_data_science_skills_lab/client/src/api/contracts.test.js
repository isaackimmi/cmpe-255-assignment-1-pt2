import { describe, expect, it } from "vitest";
import { validateSummary } from "./contracts";
import { summaryResponse } from "../test/fixtures";

describe("response contracts", () => {
  it("accepts the checked-in response shape", () => expect(validateSummary(summaryResponse)).toBe(summaryResponse));
  it("rejects malformed nested matrices", () => expect(() => validateSummary({ ...summaryResponse, metrics: { ...summaryResponse.metrics, classification: { ...summaryResponse.metrics.classification, confusion_matrix: [] } } })).toThrow(/confusion_matrix/));
});
