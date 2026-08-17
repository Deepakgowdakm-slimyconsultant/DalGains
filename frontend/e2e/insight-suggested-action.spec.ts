import { test, expect } from "@playwright/test";
import { onboardUser } from "./helpers";

// Critical path 3: an insight fires from real logged data, and tapping its
// suggested-action chip opens the log-entry flow. Note: this is the actual,
// honest behavior -- the chip opens the general log sheet, it does not
// structurally pre-fill the entry. Testing anything stronger would assert a
// feature that doesn't exist.
test("protein-deficit insight suggested-action chip opens the log sheet", async ({ page }) => {
  await onboardUser(page, "Insight E2E");
  const userId = await page.evaluate(() => localStorage.getItem("dalgains_user_id"));
  expect(userId).toBeTruthy();

  // dal_tadka_north is low-protein (~10g/serving), so 3 consecutive days of
  // just that recipe pushes every day under 80% of any reasonable protein
  // target, satisfying check_protein_deficit_3day.
  for (let i = 0; i < 3; i++) {
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

  await page.goto("/insights");
  await page.waitForLoadState("networkidle");

  await expect(page.getByText("Protein has been low for 3 days")).toBeVisible();

  const suggestionChip = page.getByRole("button", { name: /adds about/ }).first();
  await expect(suggestionChip).toBeVisible();
  await suggestionChip.click();

  await expect(page.getByRole("dialog")).toBeVisible();
});
