import { useState } from "react";
import { SectionHeader } from "../common/SectionHeader";
import { taxiApi } from "../../services/api";
import { EstimateForm } from "./EstimateForm";
import { EstimateResult } from "./EstimateResult";
import "./estimator.css";

export function TripEstimator() {
  const [state, setState] = useState({
    result: null,
    error: null,
    submitting: false,
  });
  const estimate = async (payload) => {
    setState((current) => ({ ...current, error: null, submitting: true }));
    try {
      setState({
        result: await taxiApi.estimate(payload),
        error: null,
        submitting: false,
      });
    } catch (error) {
      setState((current) => ({ ...current, error, submitting: false }));
    }
  };
  return (
    <section
      id="estimate"
      className="section estimate-section estimator-section"
    >
      <SectionHeader
        eyebrow="03 / API-backed what-if"
        title="Sketch a trip."
        description="This request is validated by FastAPI and served by the ML adapter. It mirrors the synthetic generator and is labeled as a teaching estimate."
      />
      <div className="estimate-grid">
        <EstimateForm
          onSubmit={estimate}
          submitting={state.submitting}
          error={state.error}
        />
        <EstimateResult result={state.result} />
      </div>
    </section>
  );
}
