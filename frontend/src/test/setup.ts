import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "./mocks/server";
import testI18n from "./i18n";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
  localStorage.clear();
  // The test i18n instance (src/test/i18n.ts) is a module-level
  // singleton shared across every test file in this run -- a test that
  // switches language (Profile's language-switcher test) would leak
  // that into every test that runs after it otherwise.
  testI18n.changeLanguage("en");
});
afterAll(() => server.close());
