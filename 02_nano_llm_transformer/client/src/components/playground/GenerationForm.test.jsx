import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { renderWithTheme } from "../../test/render";
import { GenerationForm } from "./GenerationForm";

describe("GenerationForm", () => {
  it("validates prompts before calling the API", async () => {
    const onGenerate = vi.fn();
    renderWithTheme(<GenerationForm onGenerate={onGenerate} requestState="ready" enabled />);
    await userEvent.clear(screen.getByLabelText("Prompt"));
    fireEvent.submit(screen.getByRole("button", { name: /generate/i }).closest("form"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Enter a prompt");
    expect(onGenerate).not.toHaveBeenCalled();
  });

  it("gates and explains generation while evidence is unavailable", () => {
    renderWithTheme(<GenerationForm onGenerate={vi.fn()} requestState="ready" enabled={false} />);
    expect(screen.getByRole("button", { name: /generate/i })).toBeDisabled();
    expect(screen.getByText(/after the model evidence service connects/i)).toHaveAttribute("role", "status");
  });

  it("disables pending requests and renders successful output", () => {
    renderWithTheme(<GenerationForm onGenerate={vi.fn()} requestState="requesting" enabled replay={{ generated: "A transformer" }} />);
    expect(screen.getByRole("button", { name: /generating/i })).toBeDisabled();
    expect(screen.getByText("A transformer")).toBeInTheDocument();
  });

  it("surfaces rejected requests in an alert", async () => {
    const onGenerate = vi.fn().mockRejectedValue(new Error("generation failed"));
    renderWithTheme(<GenerationForm onGenerate={onGenerate} requestState="ready" enabled />);
    await userEvent.click(screen.getByRole("button", { name: /generate/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("generation failed"));
  });
});
