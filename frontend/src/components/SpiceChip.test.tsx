import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { SpiceChip } from "./SpiceChip";

describe("SpiceChip", () => {
  it("renders as a non-interactive span when no onClick is given", () => {
    renderWithProviders(<SpiceChip label="Suggestion" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText("Suggestion")).toBeInTheDocument();
  });

  it("fires onClick and reports aria-pressed when interactive", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    renderWithProviders(<SpiceChip label="high_protein" selected={false} onClick={onClick} />);

    const chip = screen.getByRole("button", { name: "high_protein" });
    expect(chip).toHaveAttribute("aria-pressed", "false");
    await user.click(chip);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("light tone selected state uses coal_black text (WCAG AA fix, not signboard_white)", () => {
    renderWithProviders(<SpiceChip label="katori" selected onClick={() => {}} tone="light" />);
    expect(screen.getByRole("button").className).toContain("text-coal_black");
  });

  it("dark tone is legible on a signboard-colored card (distinct classes from light tone)", () => {
    renderWithProviders(<SpiceChip label="Swap in a bajra roti" tone="dark" onClick={() => {}} />);
    const chip = screen.getByRole("button");
    expect(chip.className).toContain("text-ink_hero");
    expect(chip.className).not.toContain("text-ink_body");
  });
});
