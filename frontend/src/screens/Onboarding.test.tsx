import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { getCurrentUserId } from "../lib/currentUser";
import { Onboarding } from "./Onboarding";

/** Every flow starts on the consent step (Part G) before the first real
 * question -- check the box and confirm to reach "What should we call
 * you?", exactly like a real user would. */
async function completeConsent(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("checkbox"));
  await user.click(screen.getByRole("button", { name: "Confirm" }));
}

describe("Onboarding", () => {
  it("shows the consent step first, then exactly one question at a time (one-question-per-screen rule)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Onboarding />);
    expect(screen.getByRole("heading", { name: "Before you continue" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "What should we call you?" })).not.toBeInTheDocument();

    await completeConsent(user);
    expect(screen.getByRole("heading", { name: "What should we call you?" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "How old are you?" })).not.toBeInTheDocument();
  });

  it("consent step links to Terms and Privacy, both keyboard-reachable", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Onboarding />);

    const termsLink = screen.getByRole("link", { name: "Terms of use" });
    const privacyLink = screen.getByRole("link", { name: "Privacy policy" });
    expect(termsLink).toHaveAttribute("href", "/terms");
    expect(privacyLink).toHaveAttribute("href", "/privacy");

    // Tab order: checkbox -> terms link -> privacy link.
    await user.tab();
    expect(screen.getByRole("checkbox")).toHaveFocus();
    await user.tab();
    expect(termsLink).toHaveFocus();
    await user.tab();
    expect(privacyLink).toHaveFocus();
  });

  it("disables Confirm on the consent step until the checkbox is checked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Onboarding />);
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();

    await user.click(screen.getByRole("checkbox"));
    expect(screen.getByRole("button", { name: "Confirm" })).toBeEnabled();
  });

  it("disables Confirm until the current question has an answer", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Onboarding />);
    await completeConsent(user);
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();

    await user.type(screen.getByPlaceholderText("Your name"), "Ravi");
    expect(screen.getByRole("button", { name: "Confirm" })).toBeEnabled();
  });

  it("advances name -> age -> sex on successive confirms", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Onboarding />);
    await completeConsent(user);

    await user.type(screen.getByPlaceholderText("Your name"), "Ravi");
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    expect(screen.getByRole("heading", { name: "How old are you?" })).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("Age in years"), "34");
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    expect(screen.getByRole("heading", { name: "What's your sex?" })).toBeInTheDocument();
  });

  it("renders fasting protocol as a real skippable choice, not a forced field", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Onboarding />);
    await completeConsent(user);

    for (const [placeholder, value] of [
      ["Your name", "Ravi"],
      ["Age in years", "34"],
    ] as const) {
      await user.type(screen.getByPlaceholderText(placeholder), value);
      await user.click(screen.getByRole("button", { name: "Confirm" }));
    }
    await user.click(screen.getByRole("button", { name: "male" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.type(screen.getByPlaceholderText("cm"), "175");
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.type(screen.getByPlaceholderText("kg"), "72");
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "moderate" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "maintain" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "vegetarian" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(screen.getByRole("heading", { name: "Do you follow a fasting routine?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "None" })).toBeInTheDocument();
  });

  it("submits the profile and persists the user id after completing the flow", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Onboarding />);
    await completeConsent(user);

    for (const [placeholder, value] of [
      ["Your name", "Ravi"],
      ["Age in years", "34"],
    ] as const) {
      await user.type(screen.getByPlaceholderText(placeholder), value);
      await user.click(screen.getByRole("button", { name: "Confirm" }));
    }
    await user.click(screen.getByRole("button", { name: "male" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.type(screen.getByPlaceholderText("cm"), "175");
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.type(screen.getByPlaceholderText("kg"), "72");
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "moderate" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "maintain" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "vegetarian" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await user.click(screen.getByRole("button", { name: "None" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByRole("heading", { name: "Here's your plan" })).toBeInTheDocument();
    // POST /profile echoes the submitted body back (see handlers.ts),
    // so the persisted id is whatever client-generated uuid was sent --
    // just assert it actually got persisted, not a specific value.
    expect(getCurrentUserId()).not.toBeNull();
  });
});
