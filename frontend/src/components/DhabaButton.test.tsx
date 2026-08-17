import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { DhabaButton } from "./DhabaButton";

describe("DhabaButton", () => {
  it("fires onClick when tapped", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    renderWithProviders(<DhabaButton onClick={onClick}>Log this</DhabaButton>);

    await user.click(screen.getByRole("button", { name: "Log this" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("does not fire onClick when disabled", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    renderWithProviders(
      <DhabaButton onClick={onClick} disabled>
        Log this
      </DhabaButton>
    );

    await user.click(screen.getByRole("button", { name: "Log this" }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("meets the 56x56 primary tap-target minimum", () => {
    renderWithProviders(<DhabaButton>Log this</DhabaButton>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("min-h-tap-primary");
    expect(button.className).toContain("min-w-tap-primary");
  });

  it("defaults to the primary variant's coal_black-on-saffron text color (WCAG AA fix)", () => {
    renderWithProviders(<DhabaButton>Log this</DhabaButton>);
    expect(screen.getByRole("button").className).toContain("text-coal_black");
  });

  it("danger variant uses the warning background", () => {
    renderWithProviders(<DhabaButton variant="danger">Reset all data</DhabaButton>);
    expect(screen.getByRole("button").className).toContain("bg-accent_warning");
  });
});
