import { beforeEach, describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { renderWithProviders } from "../test/render";
import { server } from "../test/mocks/server";
import { mockAdminUser } from "../test/mocks/fixtures";
import { setCurrentUserId } from "../lib/currentUser";
import { AuthContext } from "../lib/AuthContext";
import { Profile } from "./Profile";

const BASE = "http://localhost:8000";

describe("Profile", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("renders the current profile's editable fields", async () => {
    renderWithProviders(<Profile />);
    expect(await screen.findByDisplayValue("Asha")).toBeInTheDocument();
    expect(screen.getByDisplayValue("58")).toBeInTheDocument();
  });

  it("shows the AGPL-3.0 license and a not-medical-advice disclaimer", async () => {
    renderWithProviders(<Profile />);
    expect(await screen.findByText(/AGPL-3\.0/)).toBeInTheDocument();
    expect(screen.getByText(/not medical advice/)).toBeInTheDocument();
  });

  it("requires an explicit second confirmation before resetting data", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Profile />);
    await screen.findByDisplayValue("Asha");

    await user.click(screen.getByRole("button", { name: "Reset all data" }));
    expect(screen.getByText(/This deletes your profile and starts over/)).toBeInTheDocument();
    // The destructive action isn't available as a single tap -- only
    // after this explicit confirmation step renders.
    expect(screen.getByRole("button", { name: "Yes, reset everything" })).toBeInTheDocument();
  });

  it("switches the active language when a language chip is tapped", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Profile />);
    await screen.findByDisplayValue("Asha");

    await user.click(screen.getByRole("button", { name: "हिन्दी" }));
    await waitFor(() => expect(screen.getByText("प्रोफ़ाइल")).toBeInTheDocument());
  });

  it("labels an uncalibrated unit as default until the user sets their own", async () => {
    renderWithProviders(<Profile />);
    expect(await screen.findByText("150ml (default)")).toBeInTheDocument();
  });

  it("recalibrates a unit and shows the new value without the default label", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Profile />);

    await user.click(await screen.findByText("150ml (default)"));
    const input = screen.getByPlaceholderText("ml");
    await user.clear(input);
    await user.type(input, "180");
    // Two "Save" buttons exist (profile fields + this calibration row) --
    // the calibration one is the one rendered alongside the ml input.
    await user.click(screen.getAllByRole("button", { name: "Save" })[1]);

    await waitFor(() => expect(screen.getByText("180ml")).toBeInTheDocument());
    expect(screen.queryByText("150ml (default)")).not.toBeInTheDocument();
  });

  it("toggles dark mode and reflects the pressed state", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Profile />);
    await screen.findByDisplayValue("Asha");

    const toggle = screen.getByRole("switch", { name: "Dark mode" });
    expect(toggle).toHaveAttribute("aria-checked", "false");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-checked", "true");
  });

  it("cancels out of the reset-data confirmation without resetting", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Profile />);
    await screen.findByDisplayValue("Asha");

    await user.click(screen.getByRole("button", { name: "Reset all data" }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByText(/This deletes your profile and starts over/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset all data" })).toBeInTheDocument();
  });

  it("logs out, clearing the session and navigating to /login", async () => {
    let logoutCalled = false;
    server.use(http.post(`${BASE}/auth/logout`, () => {
      logoutCalled = true;
      return new HttpResponse(null, { status: 204 });
    }));
    const user = userEvent.setup();
    renderWithProviders(<Profile />);
    await screen.findByDisplayValue("Asha");

    await user.click(screen.getByRole("button", { name: "Log out" }));

    await waitFor(() => expect(logoutCalled).toBe(true));
  });

  it("hides the admin link for a non-admin user", async () => {
    renderWithProviders(<Profile />);
    await screen.findByDisplayValue("Asha");
    expect(screen.queryByRole("button", { name: "Invitations" })).not.toBeInTheDocument();
  });

  it("shows an admin link for an admin user", async () => {
    renderWithProviders(
      <AuthContext.Provider value={mockAdminUser}>
        <Profile />
      </AuthContext.Provider>
    );
    await screen.findByDisplayValue("Asha");
    expect(screen.getByRole("button", { name: "Invitations" })).toBeInTheDocument();
  });

  it("links to About, Terms and Privacy, each keyboard-activatable", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Profile />);
    await screen.findByDisplayValue("Asha");

    for (const name of ["About DalGains", "Terms of use", "Privacy policy"]) {
      const button = screen.getByRole("button", { name });
      button.focus();
      expect(button).toHaveFocus();
      await user.keyboard("{Enter}");
    }
  });
});
