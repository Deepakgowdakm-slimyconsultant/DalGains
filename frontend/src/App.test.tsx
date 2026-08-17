import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { setCurrentUserId } from "./lib/currentUser";

// App owns its own BrowserRouter (not injectable), so these tests drive
// it via the real browser History API rather than the renderWithProviders
// MemoryRouter wrapper used everywhere else.
function renderAppAt(path: string) {
  window.history.pushState({}, "", path);
  return render(<App />);
}

describe("App", () => {
  it("redirects to onboarding when no profile exists yet", () => {
    renderAppAt("/");
    expect(screen.getByRole("heading", { name: "What should we call you?" })).toBeInTheDocument();
  });

  it("renders Home at / once a profile exists", async () => {
    setCurrentUserId("test-user");
    renderAppAt("/");
    expect(await screen.findByText(/Asha/)).toBeInTheDocument();
  });

  it("renders the bottom nav once past onboarding", async () => {
    setCurrentUserId("test-user");
    renderAppAt("/weekly");
    expect(await screen.findByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
  });
});
