import { defineConfig, devices } from "@playwright/test";

// This environment's pre-installed Chromium build (revision 1194) predates
// the revision this @playwright/test version (1.62.1) expects (1234), so
// the default download-managed lookup misses -- point directly at the
// binary on disk instead of letting Playwright resolve it by revision.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  // Single worker: every spec drives real writes against one shared dev
  // API/data-store instance (reuseExistingServer), so parallel workers
  // race each other's log entries and timing, not just CPU -- this
  // surfaced as flaky timeouts under the default multi-worker scheduling.
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 420, height: 900 }, launchOptions: { executablePath: "/opt/pw-browsers/chromium" } },
    },
  ],
  webServer: [
    {
      command: "bash scripts/run_dev_api.sh",
      cwd: "..",
      url: "http://localhost:8000/health",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "npm run dev -- --port 5173",
      url: "http://localhost:5173",
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
