import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/render";
import { setCurrentUserId } from "../../lib/currentUser";
import { Patterns } from "./Patterns";

describe("Patterns", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("ranks most-logged meals by count using the resolved recipe name", async () => {
    renderWithProviders(<Patterns />);
    expect(await screen.findByText(/1\. Dal Tadka/)).toBeInTheDocument();
  });

  it("renders the protein-sources pie from real category attribution, not a name guess", async () => {
    renderWithProviders(<Patterns />);
    // mockCategoryBreakdown attributes 100% of protein to "dal".
    expect(await screen.findByText(/Dal \(100%\)/)).toBeInTheDocument();
  });

  it("hides fasting-window adherence for a profile with no fasting protocol", async () => {
    renderWithProviders(<Patterns />);
    await screen.findByText(/1\. Dal Tadka/);
    expect(screen.queryByText("Fasting window adherence")).not.toBeInTheDocument();
  });
});
