import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test/render";
import { About } from "./About";

// Exact wording, per the Phase 5 spec -- this isn't paraphrasable
// marketing copy, it's the legal/medical disclaimer the app commits to
// showing "without scrolling." Pinning the literal text here means a
// future i18n edit that drifts from the agreed wording fails loudly.
const MEDICAL_DISCLAIMER =
  "DalGains provides general nutrition tracking based on published Indian food composition data (IFCT 2017). It is not a substitute for advice from a doctor, registered dietitian, or other qualified health professional. Do not use DalGains to diagnose or treat any medical condition. If you have a health condition, are pregnant, or are planning significant dietary changes, consult a professional.";

const DATA_NOTICE =
  "Your logs are stored on DalGains' servers. We do not sell your data, share it with advertisers, or use it for anything beyond running the app for you. You can export or delete your data at any time from Settings.";

describe("About", () => {
  it("shows the exact medical disclaimer and data notice text", () => {
    renderWithProviders(<About />);
    expect(screen.getByText(MEDICAL_DISCLAIMER)).toBeInTheDocument();
    expect(screen.getByText(DATA_NOTICE)).toBeInTheDocument();
  });

  it("includes the AGPL footer", () => {
    renderWithProviders(<About />);
    expect(screen.getByRole("link", { name: "View source." })).toBeInTheDocument();
  });

  it("shows the admin contact once /health resolves", async () => {
    renderWithProviders(<About />);
    expect(await screen.findByText("Questions about your data? Contact admin@example.com.")).toBeInTheDocument();
  });
});
