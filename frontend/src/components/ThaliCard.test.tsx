import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { ThaliCard } from "./ThaliCard";

describe("ThaliCard", () => {
  it("renders as a non-interactive div when no onClick is given", () => {
    renderWithProviders(<ThaliCard title="Dal Tadka" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText("Dal Tadka")).toBeInTheDocument();
  });

  it("renders as a button and fires onClick when tapped", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    renderWithProviders(<ThaliCard title="Dal Tadka" onClick={onClick} />);

    await user.click(screen.getByRole("button", { name: /Dal Tadka/ }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders subtitle and meta when given", () => {
    renderWithProviders(<ThaliCard title="Dal Tadka" subtitle="Lunch" meta="180 kcal" />);
    expect(screen.getByText("Lunch")).toBeInTheDocument();
    expect(screen.getByText("180 kcal")).toBeInTheDocument();
  });

  it("meets the minimum tap-target height class", () => {
    renderWithProviders(<ThaliCard title="Dal Tadka" onClick={() => {}} />);
    expect(screen.getByRole("button").className).toContain("min-h-tap-min");
  });
});
