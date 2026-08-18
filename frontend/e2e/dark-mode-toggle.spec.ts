import { test, expect } from "@playwright/test";
import { onboardUser } from "./helpers";

// Critical path 5: the dark-mode toggle on Profile flips the `dark` class
// on <html>, which is what drives every `--color-*` custom property
// (see tailwind.config.ts's semantic-token plugin) -- checking the class
// is checking the actual mechanism, not just a visual guess.
test("dark mode toggle applies the dark class app-wide and persists it", async ({ page }) => {
  await onboardUser(page, "Dark Mode E2E");

  await expect(page.locator("html")).not.toHaveClass(/dark/);

  await page.getByRole("link", { name: "Profile" }).click();
  const darkSwitch = page.getByRole("switch", { name: "Dark mode" });
  await expect(darkSwitch).toHaveAttribute("aria-checked", "false");

  await darkSwitch.click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(darkSwitch).toHaveAttribute("aria-checked", "true");

  // Navigate away and back -- the theme choice should persist and still
  // apply on other screens, not just the one it was toggled from.
  await page.getByRole("link", { name: "Today" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);

  await page.reload();
  await expect(page.locator("html")).toHaveClass(/dark/);

  // Reset for any following test run sharing this browser context's storage.
  await page.getByRole("link", { name: "Profile" }).click();
  await page.getByRole("switch", { name: "Dark mode" }).click();
  await expect(page.locator("html")).not.toHaveClass(/dark/);
});
