import { test, expect } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { onboardViaApi, runAxe } from "./helpers";

// Mirrors design/contrast-report.md's Part F ad-hoc sweep (every core
// screen x light/dark, 18 combinations, 0 violations) as a real,
// committed assertion instead of a one-off script that only ran once.
//
// Each route/theme combination gets its own `test()` (Playwright's
// default fresh page + context per test) rather than one page walking
// all routes in a loop. That loop shape was tried first and reliably
// stalled for minutes at whichever route came 7th in the sequence,
// while a fresh page per check -- confirmed by a standalone repro
// against playwright-core -- ran every route at a steady ~10s with no
// stalls at all. Root cause not fully pinned (worth revisiting if this
// environment's Chromium build changes), but the fix is solid. Each
// test seeds an onboarded profile directly via the API (onboardViaApi)
// instead of replaying the 9-step UI wizard, since 18 fresh pages each
// running the full wizard would be its own cost.
const ROUTES = ["/", "/weekly", "/insights", "/history/timeline", "/history/trends", "/history/patterns", "/history/export", "/profile"];

test.describe("axe-core: 0 violations on every route, light and dark", () => {
  for (const theme of ["light", "dark"] as const) {
    test(`onboarding screen (${theme})`, async ({ page }) => {
      if (theme === "dark") {
        await page.addInitScript(() => localStorage.setItem("dalgains_dark_mode", "true"));
      }
      await page.goto("/onboarding");
      await page.waitForLoadState("networkidle");
      const violations = await runAxe(page);
      expect(violations, JSON.stringify(violations, null, 2)).toEqual([]);
    });

    for (const route of ROUTES) {
      test(`${route} (${theme})`, async ({ page }) => {
        if (theme === "dark") {
          await page.addInitScript(() => localStorage.setItem("dalgains_dark_mode", "true"));
        }
        await onboardViaApi(page, randomUUID(), `Axe ${theme}`);
        await page.goto(route);
        await page.waitForLoadState("networkidle");
        const violations = await runAxe(page);
        expect(violations, JSON.stringify(violations, null, 2)).toEqual([]);
      });
    }
  }
});
