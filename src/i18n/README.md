# DalGains i18n

**English (`en`) is canonical. Hindi (`hi`) and Kannada (`kn`) are opt-in
overlays.** Every screen, ingredient name, and insight message renders in
English by default; a user who wants Hindi or Kannada switches to it
explicitly via the language switcher in Profile/Settings. Nothing in the
product should assume a non-English default.

This was corrected in Phase 4 — Phase 3's scaffolding shipped with Kannada
as the primary locale, which didn't match the actual product intent. If
you're reading old code, docs, or commit messages that say "Kannada is
primary," that's the thing this file corrects.

## Rules

- **All new keys land in `locales/en.json` first.** Add the Hindi and
  Kannada translations in the same change if you can, but `en` must never
  be the locale playing catch-up.
- `src.i18n.loader.PRIMARY_LOCALE` and `FALLBACK_LOCALE` are both `"en"`.
  They're kept as separate constants because they mean different things
  (default display language vs. the reference key set for completeness
  validation) even though they currently point to the same value.
- Load-time validation (`validate_locales()` / `load_all_locales()`) still
  asserts every `en.json` key exists in `hi.json` and `kn.json` -- this
  stays useful as a completeness check regardless of which locale is
  default, and the frontend's language switcher would be broken for
  Hindi/Kannada users if it silently fell back key-by-key instead.
- Ingredient names: the canonical display is the English IFCT name. Local/
  regional names live in `Ingredient.aliases` and are used for (a) search
  matching regardless of locale, and (b) a small subtitle under the
  English name, shown only when the active locale is `hi` or `kn`. Locale
  never changes which name is authoritative, only what's shown alongside it.
- Plain language still applies in English. "Canonical" doesn't mean
  clinical -- CLAUDE.md's plain-language UX rule ("how much, roughly?"
  not "enter portion in grams") governs the English strings as much as
  the Hindi/Kannada ones.
