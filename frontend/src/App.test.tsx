import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { setCurrentUserId } from "./lib/currentUser";
import { server } from "./test/mocks/server";
import { mockUser } from "./test/mocks/fixtures";

const BASE = "http://localhost:8000";

// App owns its own BrowserRouter (not injectable), so these tests drive
// it via the real browser History API rather than the renderWithProviders
// MemoryRouter wrapper used everywhere else.
function renderAppAt(path: string) {
  window.history.pushState({}, "", path);
  return render(<App />);
}

describe("App", () => {
  it("redirects to /login when not authenticated", async () => {
    server.use(http.get(`${BASE}/auth/me`, () => new HttpResponse(null, { status: 401 })));
    renderAppAt("/");
    expect(await screen.findByText("Sign in")).toBeInTheDocument();
  });

  it("redirects to onboarding when authenticated but no profile exists yet", async () => {
    server.use(http.get(`${BASE}/profile/:userId`, () => new HttpResponse(null, { status: 404 })));
    renderAppAt("/");
    expect(await screen.findByRole("heading", { name: "What should we call you?" })).toBeInTheDocument();
  });

  it("renders Home at / once a profile exists", async () => {
    setCurrentUserId(mockUser.id);
    renderAppAt("/");
    expect(await screen.findByText(/Asha/)).toBeInTheDocument();
  });

  it("renders the bottom nav once past onboarding", async () => {
    setCurrentUserId(mockUser.id);
    renderAppAt("/weekly");
    expect(await screen.findByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
  });
});
