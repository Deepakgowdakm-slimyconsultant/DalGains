import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { LogEntryFlow } from "./LogEntryFlow";

describe("LogEntryFlow", () => {
  it("walks search -> unit -> when -> confirm and saves with a real nutrition preview", async () => {
    const user = userEvent.setup();
    const onLogged = vi.fn();
    renderWithProviders(<LogEntryFlow open userId="test-user" onClose={() => {}} onLogged={onLogged} />);

    // Step 1: search finds the seeded recipe.
    await user.type(screen.getByPlaceholderText("Search dal, sabzi, roti..."), "dal");
    const result = await screen.findByRole("button", { name: /Dal Tadka/ });
    await user.click(result);

    // Step 2: unit/servings step for a recipe entry.
    expect(await screen.findByText("1 serving(s)")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    // Step 3: when.
    expect(await screen.findByText("Just now")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Lunch" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    // Step 4: confirm with a real (not client-computed) nutrition preview,
    // editable up to this point -- never silently accepted.
    expect(await screen.findByText(/Calories: 201/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Add to today's log" }));

    await waitFor(() => expect(onLogged).toHaveBeenCalledOnce());
  });

  it("lets the user go back from confirm to edit the quantity", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LogEntryFlow open userId="test-user" onClose={() => {}} onLogged={() => {}} />);

    await user.type(screen.getByPlaceholderText("Search dal, sabzi, roti..."), "dal");
    await user.click(await screen.findByRole("button", { name: /Dal Tadka/ }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    await screen.findByText(/Calories: 201/);
    await user.click(screen.getByRole("button", { name: "Edit" }));

    expect(await screen.findByText("1 serving(s)")).toBeInTheDocument();
  });
});
