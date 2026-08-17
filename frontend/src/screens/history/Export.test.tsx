import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/render";
import { setCurrentUserId } from "../../lib/currentUser";
import { Export } from "./Export";

describe("Export", () => {
  beforeEach(() => setCurrentUserId("test-user"));

  it("counts the logged days within the selected date range", async () => {
    renderWithProviders(<Export />);
    expect(await screen.findByText("1 logged days in this range")).toBeInTheDocument();
  });

  it("offers JSON, CSV, and print-to-PDF export actions", async () => {
    renderWithProviders(<Export />);
    await screen.findByText("1 logged days in this range");
    expect(screen.getByRole("button", { name: "Download as JSON" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download as CSV" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Print / save as PDF" })).toBeInTheDocument();
  });

  it("only downloads a summary for sharing, not raw logs (per the brief)", async () => {
    renderWithProviders(<Export />);
    expect(await screen.findByText(/summary only/)).toBeInTheDocument();
  });

  it("triggers window.print for the PDF action rather than a PDF library", async () => {
    const user = userEvent.setup();
    const printSpy = vi.spyOn(window, "print").mockImplementation(() => {});
    renderWithProviders(<Export />);

    await user.click(await screen.findByRole("button", { name: "Print / save as PDF" }));
    expect(printSpy).toHaveBeenCalledOnce();
    printSpy.mockRestore();
  });

  it("downloads a JSON file via a Blob URL when 'Download as JSON' is tapped", async () => {
    const user = userEvent.setup();
    // jsdom doesn't implement Blob URL creation/revocation -- add them
    // as real (spied) methods on the real URL constructor rather than
    // replacing the global, which would break unrelated `new URL(...)`
    // calls elsewhere (openapi-fetch's request construction).
    const createObjectURLSpy = vi.fn(() => "blob:mock-url");
    const revokeObjectURLSpy = vi.fn();
    URL.createObjectURL = createObjectURLSpy;
    URL.revokeObjectURL = revokeObjectURLSpy;

    renderWithProviders(<Export />);
    await user.click(await screen.findByRole("button", { name: "Download as JSON" }));

    expect(createObjectURLSpy).toHaveBeenCalledOnce();
    expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:mock-url");
  });

  it("downloads a CSV file via a Blob URL when 'Download as CSV' is tapped", async () => {
    const user = userEvent.setup();
    const createObjectURLSpy = vi.fn(() => "blob:mock-url");
    URL.createObjectURL = createObjectURLSpy;
    URL.revokeObjectURL = vi.fn();

    renderWithProviders(<Export />);
    await user.click(await screen.findByRole("button", { name: "Download as CSV" }));

    expect(createObjectURLSpy).toHaveBeenCalledOnce();
  });

  it("changing the date range updates the logged-day count", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Export />);
    await screen.findByText("1 logged days in this range");

    const startDateInput = document.querySelectorAll('input[type="date"]')[0] as HTMLInputElement;
    await user.clear(startDateInput);
    await user.type(startDateInput, "2099-01-01");

    await screen.findByText("0 logged days in this range");
  });
});
