import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test/render";
import { KatoriProgressRing } from "./KatoriProgressRing";

describe("KatoriProgressRing", () => {
  it("exposes current/target as an accessible label, not just visually", () => {
    renderWithProviders(<KatoriProgressRing label="kcal" current={1450} target={2000} />);
    expect(screen.getByRole("img", { name: "kcal: 1450 of 2000" })).toBeInTheDocument();
  });

  it("rounds the displayed current value", () => {
    renderWithProviders(<KatoriProgressRing label="kcal" current={1449.6} target={2000} />);
    expect(screen.getByText("1450")).toBeInTheDocument();
  });

  it("shows the accent_warning stroke class when current exceeds target", () => {
    const { container } = renderWithProviders(<KatoriProgressRing label="kcal" current={2500} target={2000} colorToken="accent_success" />);
    const progressCircle = container.querySelectorAll("circle")[1];
    expect(progressCircle.getAttribute("class")).toContain("stroke-accent_warning");
  });

  it("uses the requested color token's stroke class when under target", () => {
    const { container } = renderWithProviders(<KatoriProgressRing label="protein" current={80} target={110} colorToken="accent_success" />);
    const progressCircle = container.querySelectorAll("circle")[1];
    expect(progressCircle.getAttribute("class")).toContain("stroke-accent_success");
  });

  it("does not divide by zero when target is 0", () => {
    renderWithProviders(<KatoriProgressRing label="kcal" current={0} target={0} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });
});
