import { test, expect } from "@playwright/test";
import { onboardUser, runAxe } from "./helpers";

// Mirrors design/contrast-report.md's Part F ad-hoc sweep (every core
// screen x light/dark, 18 combinations, 0 violations) as a real,
// committed assertion instead of a one-off script that only ran once.
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
        await onboardUser(page, `Axe ${theme} ${route}`);
        await page.goto(route);
        await page.waitForLoadState("networkidle");
        const violations = await runAxe(page);
        expect(violations, JSON.stringify(violations, null, 2)).toEqual([]);
      });
    }
  }
});
