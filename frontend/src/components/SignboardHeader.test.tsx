import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test/render";
import { SignboardHeader } from "./SignboardHeader";

describe("SignboardHeader", () => {
  it("renders the title as a heading", () => {
    renderWithProviders(<SignboardHeader title="Good morning, Asha" />);
    expect(screen.getByRole("heading", { name: "Good morning, Asha" })).toBeInTheDocument();
  });

  it("renders a subtitle when given", () => {
    renderWithProviders(<SignboardHeader title="Today" subtitle="Monday, August 17" />);
    expect(screen.getByText("Monday, August 17")).toBeInTheDocument();
  });

  it("omits the subtitle entirely when not given", () => {
    const { container } = renderWithProviders(<SignboardHeader title="Today" />);
    expect(container.querySelectorAll("p")).toHaveLength(0);
  });

  it("renders trailing content when given", () => {
    renderWithProviders(<SignboardHeader title="Profile" trailing={<button>Edit</button>} />);
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
  });

  it("wraps long titles instead of truncating them (regression: Onboarding question titles were clipped)", () => {
    renderWithProviders(<SignboardHeader title="Do you follow a fasting routine?" />);
    const heading = screen.getByRole("heading");
    expect(heading.className).not.toMatch(/\btruncate\b/);
  });
});
