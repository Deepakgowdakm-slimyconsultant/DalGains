import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { renderWithProviders } from "../test/render";
import { server } from "../test/mocks/server";
import { Login } from "./Login";

const BASE = "http://localhost:8000";

describe("Login", () => {
  it("disables the send button until an email is entered", () => {
    renderWithProviders(<Login />);
    expect(screen.getByRole("button", { name: "Send me a sign-in link" })).toBeDisabled();
  });

  it("requests a magic link and shows the check-your-email confirmation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Login />);

    await user.type(screen.getByLabelText("Your email"), "alice@example.com");
    await user.click(screen.getByRole("button", { name: "Send me a sign-in link" }));

    await waitFor(() => expect(screen.getByText("Check your email")).toBeInTheDocument());
    expect(screen.getByText(/alice@example.com/)).toBeInTheDocument();
  });

  it("lets the user go back and try a different email", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Login />);

    await user.type(screen.getByLabelText("Your email"), "alice@example.com");
    await user.click(screen.getByRole("button", { name: "Send me a sign-in link" }));
    await screen.findByText("Check your email");

    await user.click(screen.getByRole("button", { name: "Use a different email" }));
    expect(screen.getByRole("button", { name: "Send me a sign-in link" })).toBeInTheDocument();
  });

  it("shows an error message if the request fails", async () => {
    server.use(http.post(`${BASE}/auth/request-link`, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<Login />);

    await user.type(screen.getByLabelText("Your email"), "alice@example.com");
    await user.click(screen.getByRole("button", { name: "Send me a sign-in link" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong");
  });
});
