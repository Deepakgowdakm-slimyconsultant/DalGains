import { beforeEach, describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { setCurrentUserId } from "../lib/currentUser";
import { Home } from "./Home";

describe("Home", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("greets the user by name from their profile", async () => {
    renderWithProviders(<Home />);
    expect(await screen.findByText(/Asha/)).toBeInTheDocument();
  });

  it("shows today's calorie ring against the real plan target", async () => {
    renderWithProviders(<Home />);
    expect(await screen.findByRole("img", { name: /kcal: 201 of 1994/ })).toBeInTheDocument();
  });

  it("renders today's logged entry with its resolved recipe name, not the raw id", async () => {
    renderWithProviders(<Home />);
    expect(await screen.findByText("Dal Tadka")).toBeInTheDocument();
  });

  it("renders the active insight and dismisses it on tap", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Home />);

    expect(await screen.findByText("Protein has been low for 3 days")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => expect(screen.queryByText("Protein has been low for 3 days")).not.toBeInTheDocument());
  });

  it("opens the log-entry sheet from the + Log button", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Home />);
    await screen.findByText(/Asha/);

    await user.click(screen.getByRole("button", { name: "+ Log" }));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("prompts for today's weight and hides the prompt once logged", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Home />);

    expect(await screen.findByText("Log today's weight?")).toBeInTheDocument();
    await user.type(screen.getByPlaceholderText("kg"), "58");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(screen.getByText(/Today's weight: 58kg/)).toBeInTheDocument());
  });

  it("shows the English insight body by default", async () => {
    renderWithProviders(<Home />);
    expect(await screen.findByText(/Your protein has been under 80%/)).toBeInTheDocument();
  });
});
