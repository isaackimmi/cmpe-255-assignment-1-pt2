import { useState } from "react";
import { SectionHeader } from "../common/SectionHeader";
import { ErrorState, LoadingState } from "../common/AsyncState";
import { usePredictionSlice } from "../../hooks/usePredictionSlice";
import { ExplorerControls } from "./ExplorerControls";
import { SliceResults } from "./SliceResults";
import "./explorer.css";

export function SliceExplorer({ enabled }) {
  const [slice, setSlice] = useState("all");
  const [population, setPopulation] = useState("primary");
  const { data, loading, error } = usePredictionSlice(
    slice,
    population,
    enabled,
  );
  return (
    <section id="explorer" className="section dark explorer-section">
      <SectionHeader
        light
        eyebrow="02 / analytical explorer"
        title="Interrogate the holdout."
        description="Change the population or slice to recompute MAE, RMSE, and R² on the server from the prediction artifact."
      />
      <ExplorerControls
        {...{ slice, population }}
        onSliceChange={setSlice}
        onPopulationChange={setPopulation}
      />
      {loading && (
        <LoadingState label="Computing the selected holdout slice…" />
      )}
      {error && (
        <ErrorState
          error={error}
          message={
            error?.status === 0
              ? "The prediction service is unavailable. Confirm FastAPI is running on port 8001."
              : undefined
          }
        />
      )}
      {!loading && data && <SliceResults result={data} />}
    </section>
  );
}
