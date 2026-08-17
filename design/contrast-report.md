# Contrast report

Part F elderly-usability/accessibility pass. Every semantic color pair
actually used for text or interactive-element foreground/background in
the frontend, checked against WCAG 2.1 AA (4.5:1 for normal text, 3:1
for large text/UI components), in both light and dark mode. Ratios
computed from the token hex values in `tokens/colors.json` using the
standard relative-luminance formula (not sampled from rendered
screenshots), then spot-checked against axe-core's `color-contrast`
rule running on every core screen and both History-independent routes,
in both themes.

## Method

`(lighter_luminance + 0.05) / (darker_luminance + 0.05)`, where
luminance is the sRGB relative luminance of each color. This is the
same formula axe-core and the WCAG spec use.

## Results

| Pair | Light | Dark | Verdict |
|---|---|---|---|
| `surface_primary` bg + `ink_body` text (page body text) | 13.97:1 | 10.76:1 | PASS |
| `surface_card` bg + `ink_body` text (inputs, list items) | 16.34:1 | 8.03:1 | PASS |
| `surface_signboard` bg + `ink_hero` text (signboard headline) | 8.00:1 | 8.00:1 | PASS |
| `accent_action` bg + `coal_black` text (primary button) | 5.90:1 | 5.90:1 | PASS (fixed, see below) |
| `accent_action` bg + `signboard_white` text (primary button, before fix) | 2.77:1 | 2.77:1 | **FAIL** -- no longer used |
| `surface_primary`/`surface_card` bg + `accent_action_text` (links, qty buttons, active nav label) | 6.84:1 / 8.00:1 | 6.04:1 / 4.51:1 | PASS |
| `surface_primary`/`surface_card` bg + `accent_warning_text` (error text) | 4.70:1 / 5.50:1 | 6.73:1 / 5.02:1 | PASS |
| `accent_warning` bg + `signboard_white` text (urgent/danger badges, buttons) | 5.51:1 | 5.51:1 | PASS |
| `accent_warning`/80% opacity bg (on `surface_signboard`) + `signboard_white` text ("warn" severity badge) | 5.97:1 | 5.97:1 | PASS |
| `accent_celebration` bg + `coal_black` text (suggest severity badge) | 7.84:1 | 7.84:1 | PASS (fixed, see below) |
| `accent_celebration` bg + `ink_body` text (suggest severity badge, before fix) | 7.84:1 | 1.78:1 | **FAIL in dark mode** -- no longer used |
| `tamarind_brown`/15% opacity bg (on `surface_signboard`) + `ink_hero` text (info severity badge) | 8.00:1 | 8.00:1 | PASS (fixed, see below) |

Two pairs were checked and are **not currently used as text anywhere**
in the app (`accent_success` and `accent_celebration` as direct text
color on `surface_primary` -- 2.64:1 and 1.78:1, both failing). They're
only ever used as chart/ring fill colors today (`KatoriProgressRing`,
`charts.tsx`), which is a graphical/decorative use WCAG 1.4.3 doesn't
apply to. Flagging here as a guardrail: if a future screen ever sets
`text-accent_success` or `text-accent_celebration` directly on
`surface_primary`, it needs a same treatment as `accent_action_text`/
`accent_warning_text` below -- don't assume the semantic token name
implies its raw hex is safe as text color.

## Fixes made

Six real failures found. Four came from the manual token-pair sweep
above; the other two only surfaced by actually running axe-core against
the rendered DOM in both themes -- the info-badge case involves an
opacity blend against a specific parent background the flat token-pair
table doesn't model, and the suggest-badge case only fails in dark
mode, so a light-mode-only check would have missed it entirely. Every
fix in this section follows one rule: **a color that doesn't change
between light and dark mode (a raw palette swatch, or an accent_* token
that's deliberately unchanged across themes) needs a text color that
also doesn't change between modes.** Pairing an invariant background
with a semantic ink token that flips per-theme (`ink_body`,
`ink_hero`) is what caused three of these six failures.

1. **White text on `accent_action` (saffron_orange) buttons/chips was
   2.77:1**, not the 4.5:1 AA floor. `DhabaButton`'s primary variant,
   `SpiceChip`'s light-tone selected variant, and the History sub-nav's
   active-tab state all switched to `coal_black` text, which passes at
   5.90:1. `coal_black` (not the `ink_body` semantic token) specifically
   because `accent_action` doesn't change between light/dark mode, so
   the text color sitting on it can't either -- `ink_body` flips to a
   light color in dark mode and would recreate the same failure there.

2. **`accent_action` (saffron_orange) as inline text/link color was
   2.36-2.77:1** against light surfaces (the katori-calibration links,
   the qty +/- buttons, the active bottom-nav label). New semantic
   token `accent_action_text`: `tamarind_brown` in light mode (6.8-8:1),
   `turmeric_yellow` in dark mode (4.5-6:1, since tamarind_brown itself
   is too dark to read against the dark-mode background).

3. **`accent_warning` (chilli_red) as error-message text was 2.29:1**
   in dark mode specifically (light mode's 4.70:1 already passed). New
   semantic token `accent_warning_text`: `chilli_red` unchanged in
   light mode, `chilli_red_soft` (a synthesized 60% tint toward
   `signboard_white` -- not sourced from the reference images, see its
   palette entry) in dark mode, passing at 5.0-6.7:1.

4. **Insights' "info" severity badge (`tamarind_brown` at 15% opacity,
   sitting on the signboard card's solid `tamarind_brown`) with
   `ink_body` (dark) text was 2.04:1** -- the badge's own background is
   effectively just `tamarind_brown` once blended with its parent, so
   it needed light text like the other severity badges, not dark.
   Switched to `ink_hero`, now 8.00:1.

5. **Insights' "suggest" severity badge (`accent_celebration`/
   turmeric_yellow bg + `ink_body` text) was 7.84:1 in light mode but
   1.78:1 in dark mode** -- `accent_celebration` doesn't change between
   themes, but `ink_body` does (it flips from `coal_black` to
   `dhaba_cream`), so the pair that worked in light mode broke in dark.
   Same root cause and same fix as #1: switched to the mode-invariant
   `coal_black` directly, not a semantic token that itself varies by
   theme.

6. Landmark/structure findings from axe-core unrelated to color but
   fixed in the same pass: every routed screen now sits inside a
   `<main>` element (`AppShell`, `Onboarding`); Weekly's horizontal
   scrolling ring strip got `tabindex="0"` + `role="region"` so
   keyboard users can actually reach it (axe's
   `scrollable-region-focusable`); and Export's two date-range inputs
   got `aria-label`s (axe's `label` rule -- they had no programmatic
   label at all before).

## Verification

axe-core 4.13 (`axe.run()`, default ruleset) against every core screen
(Home, Weekly, Insights, Profile, all four History tabs, Onboarding),
in both light and dark mode -- 18 route/theme combinations total: **0
violations**, confirmed on a full re-run after every fix above,
including the dark-mode-only suggest-badge regression that a
light-mode-only pass would have missed.

## Not covered here

This report is about *color* contrast. Font-size and tap-target
minimums are covered separately by this same Part F pass (18px mobile
body text, 56x56 primary tap targets, big-text mode) rather than
duplicated in this file.
