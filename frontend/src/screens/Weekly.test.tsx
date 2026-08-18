import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test/render";
import { setCurrentUserId } from "../lib/currentUser";
import { Weekly } from "./Weekly";

describe("Weekly", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("renders the adherence and streak stats from the real backend shape", async () => {
    renderWithProviders(<Weekly />);
    expect(await screen.findByText("7")).toBeInTheDocument(); // streak_days
    expect(screen.getByText("0%")).toBeInTheDocument(); // target_adherence_pct
  });

  it("renders a ring for each of the 7 days in the summary", async () => {
    renderWithProviders(<Weekly />);
    await screen.findByText("7");
    expect(screen.getAllByRole("img")).toHaveLength(7);
  });

  it("renders the notable-days list", async () => {
    renderWithProviders(<Weekly />);
    expect(await screen.findByText(/Highest kcal: 2026-08-11/)).toBeInTheDocument();
  });
});
