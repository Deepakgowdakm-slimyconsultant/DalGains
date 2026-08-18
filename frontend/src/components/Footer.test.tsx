import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { Footer } from "./Footer";

// AGPL-3.0 requires this notice+link to be reachable from every screen
// (see LICENSE) -- these tests pin the exact behaviour so a future
// refactor can't quietly drop it.
describe("Footer", () => {
  it("shows the AGPL notice with a link to the source repository", () => {
    renderWithProviders(<Footer />);
    expect(screen.getByText(/DalGains is open source \(AGPL-3\.0\)/)).toBeInTheDocument();

    const link = screen.getByRole("link", { name: "View source." });
    expect(link).toHaveAttribute("href", "https://github.com/Deepakgowdakm-slimyconsultant/DalGains");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("is keyboard-reachable (tab lands on the source link)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Footer />);
    await user.tab();
    expect(screen.getByRole("link", { name: "View source." })).toHaveFocus();
  });
});
