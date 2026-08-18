import { test, expect } from "@playwright/test";
import { onboardUser } from "./helpers";

// Critical path 2: Weekly view renders correctly after 7 days of seeded logs.
test("weekly view after 7 days of logs shows a 7-day streak and real totals", async ({ page }) => {
  await onboardUser(page, "Weekly E2E");
  const userId = await page.evaluate(() => localStorage.getItem("dalgains_user_id"));
  expect(userId).toBeTruthy();

  // Seed 7 consecutive days directly against the real backend -- driving
  // this through the UI 7 times would be slow and brittle for what's
  // fundamentally a backend-aggregation check.
  for (let i = 0; i < 7; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const iso = date.toISOString().slice(0, 10);
    const response = await page.request.post(`http://localhost:8000/logs/${userId}/entries`, {
      data: {
        recipe_id: "dal_tadka_north",
        qty: 1,
        unit: "serving",
        timestamp: `${iso}T13:00:00Z`,
        outside_eating_window: false,
      },
    });
    expect(response.ok()).toBe(true);
  }

  await page.goto("/weekly");
  await page.waitForLoadState("networkidle");

  await expect(page.getByText("7", { exact: true })).toBeVisible();
  await expect(page.getByText("Day streak")).toBeVisible();
  await expect(page.getByRole("img")).toHaveCount(7);
  await expect(page.getByText(/Highest kcal:/)).toBeVisible();
});
