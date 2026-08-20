import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test/render";
import { Privacy } from "./Privacy";

describe("Privacy", () => {
  it("renders, includes DPDP Act acknowledgment, and the AGPL footer", async () => {
    renderWithProviders(<Privacy />);
    expect(screen.getByRole("heading", { name: "Privacy policy" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "DPDP Act 2023" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View source." })).toBeInTheDocument();
  });

  it("shows the admin contact once /health resolves", async () => {
    renderWithProviders(<Privacy />);
    expect(await screen.findByText("For data access, correction, or deletion requests: admin@example.com.")).toBeInTheDocument();
  });
});
