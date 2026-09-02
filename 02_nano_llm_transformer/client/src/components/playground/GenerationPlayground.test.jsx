import { screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { describe, expect, it, vi } from "vitest";
import { renderWithTheme } from "../../test/render";
import { GenerationPlayground } from "./GenerationPlayground";

const replay = {
  generated: "abc",
  deterministic: true,
  context_order: 3,
  trace: [{ step: 1, context: "ser", selected: ":", candidates: [{ token: ":", probability: 1 }] }],
};

describe("GenerationPlayground", () => {
  it("composes probability and trace evidence semantically", () => {
    renderWithTheme(<GenerationPlayground metrics={{ behavior: { order: 3 } }} onGenerate={vi.fn()} replay={replay} requestState="complete" enabled />);
    expect(screen.getByRole("heading", { name: "Watch the next character happen." })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Next-character probability distribution" })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Generation trace" })).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: ": probability" })).toHaveAttribute("aria-valuenow", "100");
  });

  it("has no basic accessibility violations", async () => {
    const { container } = renderWithTheme(<GenerationPlayground metrics={{}} onGenerate={vi.fn()} replay={replay} requestState="complete" enabled />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
