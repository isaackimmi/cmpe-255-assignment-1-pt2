import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../App";

const workspace = {
  project: { name: "Retail demand forecast", brief: "Plan demand", goal: "Reduce stock-outs." },
  readiness: { status: "PLANNED", dataset: "retail_orders.parquet", score: 0, note: "No dataset connected.", boundary: "planning-only · no model artifact" },
  tasks: [
    { id: 1, title: "Capture business constraints", area: "Business understanding", priority: "high", done: true },
    { id: 2, title: "Validate holiday flags", area: "Data preparation", priority: "medium", done: false },
  ],
  workflow: {
    current: "Modeling phase",
    stages: [
      { name: "Business understanding", status: "complete", evidence: "Goal captured", detail: "Define the stock-out objective." },
      { name: "Modeling", status: "planned", evidence: "Baseline planned", detail: "Compare against seasonal naive." },
    ],
  },
  activity: [],
};

function response(body, status = 200) {
  return Promise.resolve({ ok: status >= 200 && status < 300, status, text: async () => JSON.stringify(body) });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(() => response(workspace)));
});

describe("Fieldnote React client", () => {
  it("loads the API workspace, filters tasks, and exposes workflow selection", async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading workspace");
    await screen.findByRole("heading", { name: /Make the next/i });

    await user.click(screen.getByRole("button", { name: "To do 1" }));
    expect(screen.queryByText("Capture business constraints")).not.toBeInTheDocument();
    expect(screen.getByText("Validate holiday flags")).toBeInTheDocument();

    const stage = screen.getByRole("button", { name: /Business understanding/ });
    expect(stage).toHaveAttribute("aria-pressed", "false");
    await user.click(stage);
    expect(stage).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("Selected workflow evidence")).toHaveTextContent("Define the stock-out objective");
  });

  it("renders a useful API failure state", async () => {
    fetch.mockImplementationOnce(() => response({ detail: "artifact unavailable" }, 503));
    render(<App />);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("artifact unavailable");
    expect(alert).toHaveTextContent("Expected API base: /api");
  });

  it("keeps form values and reports the error when creation fails", async () => {
    const user = userEvent.setup();
    fetch.mockImplementation((url, options = {}) => options.method === "POST" ? response({ detail: "write rejected" }, 500) : response(workspace));
    render(<App />);
    await screen.findByRole("heading", { name: /Make the next/i });
    await user.click(screen.getByRole("button", { name: /Add task/ }));
    const input = screen.getByPlaceholderText("e.g. Check holiday seasonality");
    await user.type(input, "Audit promotion flags");
    await user.click(screen.getByRole("button", { name: "Add" }));
    expect(await screen.findByText("Could not save: write rejected")).toBeInTheDocument();
    expect(input).toHaveValue("Audit promotion flags");
  });

  it("disables conflicting writes until the active mutation settles", async () => {
    const user = userEvent.setup();
    let release;
    const pendingWrite = new Promise((resolve) => { release = resolve; });
    fetch.mockImplementation((url, options = {}) => options.method === "POST" ? pendingWrite : response(workspace));
    render(<App />);
    await screen.findByRole("heading", { name: /Make the next/i });
    await user.click(screen.getByRole("button", { name: /Add task/ }));
    await user.type(screen.getByPlaceholderText("e.g. Check holiday seasonality"), "Check lag policy");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(screen.getByRole("button", { name: /Run a demo check/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Delete Capture business constraints/ })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: /Complete Capture business constraints/ })).toBeDisabled();

    release({ ok: true, status: 200, text: async () => JSON.stringify(workspace.tasks) });
    await waitFor(() => expect(screen.getByText("Saved")).toBeInTheDocument());
  });

  it("refreshes workspace evidence after the demo agent check", async () => {
    const user = userEvent.setup();
    const refreshed = { ...workspace, tasks: [...workspace.tasks, { id: 3, title: "Review queue", area: "Workspace", priority: "low", done: false }] };
    let workspaceReads = 0;
    fetch.mockImplementation((url, options = {}) => {
      if (options.method === "POST") return response({ status: "demo-only" });
      workspaceReads += 1;
      return response(workspaceReads > 1 ? refreshed : workspace);
    });
    render(<App />);
    await screen.findByRole("heading", { name: /Make the next/i });
    await user.click(screen.getByRole("button", { name: /Run a demo check/ }));
    expect(await screen.findByText("Review queue")).toBeInTheDocument();
  });
});
