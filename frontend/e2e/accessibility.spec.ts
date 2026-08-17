import { test, expect } from "@playwright/test";
import { onboardUser, runAxe } from "./helpers";

// Mirrors design/contrast-report.md's Part F ad-hoc sweep (every core
// screen x light/dark, 18 combinations, 0 violations) as a real,
// committed assertion instead of a one-off script that only ran once.
//
// One onboarded session is reused across all routes for a given theme
// (rather than onboarding fresh per route) -- 18 full onboarding wizard
// runs back-to-back was the single biggest cost in this suite and, in
// this environment's headless Chromium, pushed some runs into multi-
// minute stalls. Two onboarding runs plus 16 in-session navigations is
// both faster and closer to how a real user actually hits these routes.
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

    test(`all core routes (${theme})`, async ({ page }) => {
      test.setTimeout(180_000);
      if (theme === "dark") {
        await page.addInitScript(() => localStorage.setItem("dalgains_dark_mode", "true"));
      }
      await onboardUser(page, `Axe ${theme}`);

      for (const route of ROUTES) {
        await test.step(route, async () => {
          await page.goto(route);
          await page.waitForLoadState("networkidle");
          const violations = await runAxe(page);
          expect(violations, JSON.stringify(violations, null, 2)).toEqual([]);
        });
      }
    });
  }
});
