import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/render";
import { HistoryLayout } from "./HistoryLayout";

describe("HistoryLayout", () => {
  it("renders all four History sub-tabs as real links", () => {
    renderWithProviders(<HistoryLayout />, { route: "/history/timeline" });
    for (const label of ["Timeline", "Trends", "Patterns", "Export"]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
    }
  });

  it("marks the current tab active", () => {
    renderWithProviders(<HistoryLayout />, { route: "/history/trends" });
    expect(screen.getByRole("link", { name: "Trends" }).className).toContain("bg-accent_action");
    expect(screen.getByRole("link", { name: "Timeline" }).className).not.toContain("bg-accent_action");
  });
});
