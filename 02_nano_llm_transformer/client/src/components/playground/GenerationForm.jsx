import { useState } from "react";
import { Button, Callout, TextArea, TextField } from "@radix-ui/themes";
import { Panel } from "../ui";

const DEFAULT_PROMPT = "user: explain a transformer\nassistant:";

export function GenerationForm({ onGenerate, replay, requestState, requestError = "", enabled = true }) {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [maxNewTokens, setMaxNewTokens] = useState(16);
  const [temperature, setTemperature] = useState(0);
  const [localError, setLocalError] = useState("");
  const pending = requestState === "requesting";

  async function submit(event) {
    event.preventDefault();
    setLocalError("");
    const tokens = Number(maxNewTokens);
    const heat = Number(temperature);
    if (!prompt.trim()) {
      setLocalError("Enter a prompt before generating.");
      return;
    }
    if (!Number.isInteger(tokens) || tokens < 1 || tokens > 80) {
      setLocalError("New characters must be a whole number from 1 to 80.");
      return;
    }
    if (!Number.isFinite(heat) || heat < 0 || heat > 2) {
      setLocalError("Temperature must be between 0 and 2.");
      return;
    }
    try {
      await onGenerate({ prompt, maxNewTokens: tokens, temperature: heat });
    } catch (error) {
      setLocalError(`Request error: ${error.message}`);
    }
  }

  return (
    <Panel className="generation-form-card">
      <div className="chat-head"><strong>Generation request</strong><span aria-live="polite">{requestState}</span></div>
      <form className="generation-form" onSubmit={submit} aria-describedby={!enabled ? "generation-disabled-reason" : undefined}>
        <label htmlFor="prompt">Prompt</label>
        <TextArea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} rows="3" maxLength={500} required />
        <div className="form-row">
          <label htmlFor="max-tokens">New characters<TextField.Root id="max-tokens" type="number" min="1" max="80" value={maxNewTokens} onChange={(event) => setMaxNewTokens(event.target.value)} /></label>
          <label htmlFor="temperature">Temperature<TextField.Root id="temperature" type="number" min="0" max="2" step="0.1" value={temperature} onChange={(event) => setTemperature(event.target.value)} /></label>
          <Button type="submit" size="3" disabled={pending || !enabled}>{pending ? "Generating…" : "Generate ↗"}</Button>
        </div>
        {!enabled && <p className="generation-disabled" id="generation-disabled-reason" role="status">Generation becomes available after the model evidence service connects.</p>}
      </form>
      {(localError || requestError) && <Callout.Root className="request-error" color="red" role="alert"><Callout.Text>{localError || `Request error: ${requestError}`}</Callout.Text></Callout.Root>}
      <div className="generation-response" aria-live="polite" aria-atomic="true">
        <span>MODEL RESPONSE</span>
        <output>{replay?.generated || "Submit a prompt to inspect the model response."}</output>
      </div>
    </Panel>
  );
}
