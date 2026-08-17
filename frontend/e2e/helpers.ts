import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const thisDir = dirname(fileURLToPath(import.meta.url));
export const AXE_PATH = resolve(thisDir, "../node_modules/axe-core/axe.min.js");

/** Drives the full onboarding wizard end-to-end against the real
 * backend (no mocking in e2e -- that's what component tests are for).
 * Leaves the page on Home afterward. */
export async function onboardUser(page: Page, name = "E2E Test User") {
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  await page.getByPlaceholder("Your name").fill(name);
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByPlaceholder("Age in years").fill("30");
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByRole("button", { name: "female" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByPlaceholder("cm").fill("165");
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByPlaceholder("kg").fill("60");
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByRole("button", { name: "moderate" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByRole("button", { name: "maintain" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByRole("button", { name: "vegetarian", exact: true }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await page.getByRole("button", { name: "None" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(page.getByRole("heading", { name: "Here's your plan" })).toBeVisible();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(page.getByRole("heading", { name: "Let's set up your katori" })).toBeVisible();
  await page.getByRole("button", { name: "Use defaults, calibrate later" }).click();

  await page.waitForURL("**/");
}

export interface AxeViolation {
  id: string;
  impact: string | null;
  nodes: number;
}

/** Injects the real axe-core bundle and runs it against the current
 * page -- same library, same default ruleset used throughout this
 * phase's ad-hoc accessibility passes (design/contrast-report.md),
 * now as a real assertion in the suite instead of a one-off script. */
export async function runAxe(page: Page): Promise<AxeViolation[]> {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    // @ts-expect-error -- axe is attached to window by the injected script tag
    const results = await window.axe.run();
    return results.violations.map((v: { id: string; impact: string | null; nodes: unknown[] }) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.length,
    }));
  });
}
