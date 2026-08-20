import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test/render";
import { Terms } from "./Terms";

describe("Terms", () => {
  it("renders and includes the AGPL footer", () => {
    renderWithProviders(<Terms />);
    expect(screen.getByRole("heading", { name: "Terms of use" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View source." })).toBeInTheDocument();
  });
});
