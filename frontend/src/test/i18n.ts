// Test-only i18n instance: loads the real locale JSON synchronously via
// readFileSync (Vitest runs in Node, not a browser) instead of the app's
// i18next-http-backend, which fetches from a dev-server-served static
// path that doesn't exist under the test runner. Same source of truth
// (src/i18n/locales/*.json) as the real app -- no duplicated strings.
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const thisDir = dirname(fileURLToPath(import.meta.url));
const localesDir = resolve(thisDir, "../../../src/i18n/locales");
const loadLocale = (lng: string) => JSON.parse(readFileSync(`${localesDir}/${lng}.json`, "utf-8"));

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    lng: "en",
    fallbackLng: "en",
    resources: {
      en: { translation: loadLocale("en") },
      hi: { translation: loadLocale("hi") },
      kn: { translation: loadLocale("kn") },
    },
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });
}

export default i18n;
