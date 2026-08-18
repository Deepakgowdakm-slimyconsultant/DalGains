import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { FloatingLogSheet } from "./FloatingLogSheet";

describe("FloatingLogSheet", () => {
  it("renders nothing when closed", () => {
    renderWithProviders(
      <FloatingLogSheet open={false} title="How much, roughly?" onClose={() => {}}>
        <p>content</p>
      </FloatingLogSheet>
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders as a labeled dialog with its children when open", () => {
    renderWithProviders(
      <FloatingLogSheet open title="How much, roughly?" onClose={() => {}}>
        <p>Sheet content</p>
      </FloatingLogSheet>
    );
    const dialog = screen.getByRole("dialog", { name: "How much, roughly?" });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText("Sheet content")).toBeInTheDocument();
  });

  it("calls onClose when the close button is tapped", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(
      <FloatingLogSheet open title="How much, roughly?" onClose={onClose}>
        <p>content</p>
      </FloatingLogSheet>
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
