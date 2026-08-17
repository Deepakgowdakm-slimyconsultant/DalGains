import { test, expect } from "@playwright/test";
import { onboardUser } from "./helpers";

// Critical path 4: switching language on Profile swaps visible text
// app-wide, including the bottom nav (outside the Profile screen itself).
test("language switcher swaps nav and screen text to Hindi", async ({ page }) => {
  await onboardUser(page, "Language E2E");

  await expect(page.getByRole("link", { name: "Today" })).toBeVisible();

  await page.getByRole("link", { name: "Profile" }).click();
  await expect(page.getByRole("heading", { name: "Profile" })).toBeVisible();

  await page.getByRole("button", { name: "हिन्दी" }).click();

  await expect(page.getByRole("heading", { name: "प्रोफ़ाइल" })).toBeVisible();
  await expect(page.getByRole("link", { name: "आज" })).toBeVisible();
  await expect(page.getByRole("link", { name: "प्रोफ़ाइल" })).toBeVisible();

  // Switch back to English so it doesn't leak into other test runs sharing
  // this browser's localStorage-persisted i18n choice.
  await page.getByRole("button", { name: "English" }).click();
  await expect(page.getByRole("heading", { name: "Profile" })).toBeVisible();
});
