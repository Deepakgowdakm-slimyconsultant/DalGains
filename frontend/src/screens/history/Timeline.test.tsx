import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/render";
import { setCurrentUserId } from "../../lib/currentUser";
import { Timeline } from "./Timeline";

describe("Timeline", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("renders the logged day with its date and kcal total", async () => {
    renderWithProviders(<Timeline />);
    expect(await screen.findByText(/kcal · 1/)).toBeInTheDocument();
  });

  it("expands a day on tap to show its entries", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Timeline />);
    const dayButton = await screen.findByRole("button", { name: /kcal · 1/ });

    expect(screen.queryByText("Dal Tadka")).not.toBeInTheDocument();
    await user.click(dayButton);
    expect(await screen.findByText("Dal Tadka")).toBeInTheDocument();
  });

  it("renders every filter chip from the spec", async () => {
    renderWithProviders(<Timeline />);
    await screen.findByRole("button", { name: /kcal · 1/ });
    for (const label of ["High protein", "Over target", "Under target", "On target", "Festival days", "Fasting days", "Beverages only"]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
  });

  it("filters out non-matching days when a filter is selected", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Timeline />);
    await screen.findByRole("button", { name: /kcal · 1/ });

    // The one seeded day is 201 kcal against a 1994 target -- well under,
    // so "Over target" should leave nothing.
    await user.click(screen.getByRole("button", { name: "Over target" }));
    expect(await screen.findByText("No days match this filter yet")).toBeInTheDocument();
  });
});
