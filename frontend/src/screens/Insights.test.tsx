import { beforeEach, describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { setCurrentUserId } from "../lib/currentUser";
import { Insights } from "./Insights";

describe("Insights", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("renders the insight's title, severity, and body", async () => {
    renderWithProviders(<Insights />);
    expect(await screen.findByText("Protein has been low for 3 days")).toBeInTheDocument();
    expect(screen.getByText("Suggestion")).toBeInTheDocument();
  });

  it("reveals evidence as readable key/value rows behind Show why", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Insights />);
    await screen.findByText("Protein has been low for 3 days");

    expect(screen.queryByText("days running")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show why" }));
    expect(screen.getByText("days running")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders suggested actions as tappable chips", async () => {
    renderWithProviders(<Insights />);
    expect(await screen.findByRole("button", { name: /Rajma Chawal adds about 15g protein/ })).toBeInTheDocument();
  });

  it("moves a dismissed insight into the Dismissed today section and back on restore", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Insights />);
    await screen.findByText("Protein has been low for 3 days");

    await user.click(screen.getByRole("button", { name: "Done" }));
    await waitFor(() => expect(screen.getByText("Dismissed today")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Bring back" }));
    await waitFor(() => expect(screen.queryByText("Dismissed today")).not.toBeInTheDocument());
  });
});
