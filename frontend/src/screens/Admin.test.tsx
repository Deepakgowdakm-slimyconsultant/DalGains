import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { renderWithProviders } from "../test/render";
import { server } from "../test/mocks/server";
import { Admin } from "./Admin";

const BASE = "http://localhost:8000";

describe("Admin", () => {
  it("shows an empty state when no one has been invited yet", async () => {
    renderWithProviders(<Admin />);
    expect(await screen.findByText("No one's been invited yet.")).toBeInTheDocument();
  });

  it("lists existing invitations with their status", async () => {
    server.use(
      http.get(`${BASE}/admin/invitations`, () =>
        HttpResponse.json([
          { email: "pending@example.com", invited_by: "admin@example.com", created_at: "2026-01-01T00:00:00Z", accepted_at: null, revoked_at: null },
          {
            email: "signedin@example.com",
            invited_by: "admin@example.com",
            created_at: "2026-01-01T00:00:00Z",
            accepted_at: "2026-01-02T00:00:00Z",
            revoked_at: null,
          },
        ])
      )
    );
    renderWithProviders(<Admin />);

    expect(await screen.findByText("pending@example.com")).toBeInTheDocument();
    expect(screen.getByText("Invited, not yet signed in")).toBeInTheDocument();
    expect(screen.getByText("signedin@example.com")).toBeInTheDocument();
    expect(screen.getByText("Signed in")).toBeInTheDocument();
  });

  it("invites a new email and refreshes the list", async () => {
    // Stateful within this test's closure so the GET after the POST
    // reflects the new invitation -- MSW handlers are otherwise static.
    let invited = false;
    server.use(
      http.get(`${BASE}/admin/invitations`, () =>
        HttpResponse.json(
          invited
            ? [{ email: "newperson@example.com", invited_by: "admin@example.com", created_at: "2026-01-01T00:00:00Z", accepted_at: null, revoked_at: null }]
            : []
        )
      ),
      http.post(`${BASE}/admin/invitations`, () => {
        invited = true;
        return HttpResponse.json(
          { email: "newperson@example.com", invited_by: "admin@example.com", created_at: "2026-01-01T00:00:00Z", accepted_at: null, revoked_at: null },
          { status: 201 }
        );
      })
    );
    const user = userEvent.setup();
    renderWithProviders(<Admin />);
    await screen.findByText("No one's been invited yet.");

    await user.type(screen.getByLabelText("Your email"), "newperson@example.com");
    await user.click(screen.getByRole("button", { name: "Invite" }));

    await waitFor(() => expect(screen.getByText("newperson@example.com")).toBeInTheDocument());
  });

  it("revokes an invitation", async () => {
    // Stateful within this test's closure so the GET after the DELETE
    // reflects the revocation -- MSW handlers are otherwise static.
    let revoked = false;
    server.use(
      http.get(`${BASE}/admin/invitations`, () =>
        HttpResponse.json([
          {
            email: "pending@example.com",
            invited_by: "admin@example.com",
            created_at: "2026-01-01T00:00:00Z",
            accepted_at: null,
            revoked_at: revoked ? "2026-01-03T00:00:00Z" : null,
          },
        ])
      ),
      http.delete(`${BASE}/admin/invitations/:email`, () => {
        revoked = true;
        return HttpResponse.json({
          email: "pending@example.com",
          invited_by: "admin@example.com",
          created_at: "2026-01-01T00:00:00Z",
          accepted_at: null,
          revoked_at: "2026-01-03T00:00:00Z",
        });
      })
    );
    const user = userEvent.setup();
    renderWithProviders(<Admin />);
    await screen.findByText("pending@example.com");

    await user.click(screen.getByRole("button", { name: "Revoke" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Revoke" })).not.toBeInTheDocument());
    expect(screen.getByText("Revoked")).toBeInTheDocument();
  });
});
