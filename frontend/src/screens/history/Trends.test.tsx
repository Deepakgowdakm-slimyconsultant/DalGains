import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/render";
import { setCurrentUserId } from "../../lib/currentUser";
import { Trends } from "./Trends";

describe("Trends", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("renders the calorie, macro, and adherence charts", async () => {
    renderWithProviders(<Trends />);
    expect(await screen.findByRole("heading", { name: "Calories" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Protein, fat, carbs and fiber" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Adherence" })).toBeInTheDocument();
  });

  it("does not render the weight chart when the user has never logged weight", async () => {
    renderWithProviders(<Trends />);
    await screen.findByRole("heading", { name: "Calories" });
    expect(screen.queryByRole("heading", { name: "Weight" })).not.toBeInTheDocument();
  });

  it("renders line charts as accessible role=img elements", async () => {
    renderWithProviders(<Trends />);
    expect(await screen.findAllByRole("img", { name: "Trend chart" })).not.toHaveLength(0);
  });
});
