import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Separate from vite.config.ts (not merged via vitest's mergeConfig)
// because the PWA plugin's build-time service-worker generation has no
// business running under the test runner -- component tests never see
// a service worker. CSS/Tailwind processing is skipped entirely here:
// jsdom doesn't do real layout/paint, so asserting computed styles from
// these tests wouldn't mean anything -- visual/token correctness is
// covered by the Playwright screenshot verification done throughout
// this phase, not by unit tests. Component tests assert DOM structure,
// text, and behavior.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: false,
    // Playwright's e2e/*.spec.ts files use Playwright's own `test()`, not
    // Vitest's -- exclude the directory so Vitest's default *.spec.ts glob
    // doesn't try to run them as component tests.
    exclude: ["node_modules/**", "e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "text-summary", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/api/schema.gen.ts", "src/main.tsx", "src/test/**", "**/*.d.ts"],
      // A real floor, not a rubber stamp: set a few points below what
      // this phase actually achieved (~80/67/76/86 -- see the Phase 4
      // report), so `npm run test:coverage` fails on a real regression
      // instead of always passing. Raise these as coverage improves;
      // never lower them to make a failing run pass.
      thresholds: {
        statements: 75,
        branches: 60,
        functions: 70,
        lines: 80,
      },
    },
  },
});
