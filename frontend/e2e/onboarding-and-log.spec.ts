import { test, expect } from "@playwright/test";
import { onboardUser } from "./helpers";

// Critical path 1: onboarding -> first log -> Today view shows the entry.
test("onboarding through first log shows up on Today", async ({ page }) => {
  await onboardUser(page, "Onboarding E2E");

  await expect(page.getByText(/Onboarding E2E/)).toBeVisible();
  await expect(page.getByText("Nothing logged yet today")).toBeVisible();

  await page.getByRole("button", { name: "+ Log" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();

  await page.getByPlaceholder("Search dal, sabzi, roti...").fill("dal");
  await page.getByRole("button", { name: /Dal Tadka/ }).click();

  await expect(page.getByText("1 serving(s)")).toBeVisible();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(page.getByText("Just now")).toBeVisible();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(page.getByText(/Calories: \d/)).toBeVisible();
  await page.getByRole("button", { name: "Add to today's log" }).click();

  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(page.getByText("Dal Tadka")).toBeVisible();
  await expect(page.getByText("Nothing logged yet today")).not.toBeVisible();
});
