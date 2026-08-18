import i18n from "i18next";
import Backend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

// en is canonical and the default everywhere; hi/kn are opt-in overlays
// switched via the language switcher in Profile/Settings. See
// src/i18n/README.md (backend) for the full precedence rule this mirrors.
export const SUPPORTED_LOCALES = ["en", "hi", "kn"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: DEFAULT_LOCALE,
    supportedLngs: SUPPORTED_LOCALES,
    // Only a stored/explicit choice should move a user off English --
    // browser-language sniffing is deliberately excluded, since "en
    // default unless the user actively switches" is the product rule.
    detection: {
      order: ["localStorage"],
      lookupLocalStorage: "dalgains_locale",
      caches: ["localStorage"],
    },
    backend: {
      loadPath: "/locales/{{lng}}/translation.json",
    },
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
