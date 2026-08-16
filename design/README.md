# DalGains design system — foundation

Tokens only in this phase (colors, typography, spacing, motif specs) — no
components or screens yet. Framework choice for the actual frontend is a
Phase 4 decision; the JSON files in `tokens/` are deliberately
framework-agnostic so that choice doesn't need to be made first.

## Aesthetic thesis

Three reference images set the visual direction for this phase (not
included in this repo — see the Phase 3 session that specified them).
They share one language, and it's the opposite of what most calorie
trackers look like:

1. **Devanagari (and by extension Kannada) is the hero visual element,
   not decoration.** The largest, boldest thing on each reference screen
   is a headline in Devanagari script — "अगली बस आ गई है।",
   "हॉर्न ओके प्लीज़", "डीलक्स सैलून" — rendered at a size and weight that
   would be a Latin wordmark in most apps. DalGains should default to
   this, not treat regional scripts as a translated afterthought bolted
   onto a Latin-first layout.

2. **Hand-painted Indian signboard aesthetic.** Dhaba menu boards, "shuddh
   deshi ghee" shop signs, hand-lettered hoardings, truck-art lettering.
   Not clip-art "ethnic" decoration — actual reference to how shopfronts
   and signage in Indian towns are hand-painted, including their
   imperfections (uneven strokes, slightly inconsistent letterforms, worn
   edges).

3. **Warm, saturated, painterly palette.** Sunset oranges, tamarind
   browns, chilli reds, mint greens, saffron, deep indigos. See
   `tokens/colors.json` for the extracted palette and which reference
   each color was pulled from.

4. **Subject matter is everyday India** — chai stalls, truck stops, bus
   stands, saloons — not templed/festival India, not glossy tech India.
   This matters for the motif catalog (`tokens/motifs.json`): the icons
   DalGains reaches for should be a katori, a chai glass, a sabzi crate —
   not generic "Indian" iconography.

5. **Small floating UI elements sit on top of illustrated scenes without
   breaking the mood.** The CTA buttons, music-player widgets, and status
   pills in the references are compact, high-contrast, and clearly
   "interface," but their color and shape still belong to the same warm
   palette as the illustration behind them — they don't look like a
   generic app dropped onto a picture.

## Why this matters for DalGains specifically

The whole point is that DalGains should not look like MyFitnessPal with
Hindi labels. A tracker aimed at Indian households — teenagers to
grandparents, per CLAUDE.md's UX rules — earns trust partly through
visual familiarity: it should look like it belongs in the same world as
the shop signs and menus its users see every day, not like a Silicon
Valley fitness app that got localized.

## Token-to-reference map

| Token file | What it encodes | Pulled from |
|---|---|---|
| `tokens/colors.json` | 11-color palette + semantic role aliases | Signboard colors (ghee shop, tea stall), dusk sky, bus body cream, hero-text white |
| `tokens/typography.json` | Devanagari/Kannada/Latin display fonts + a shared body-text stack, sized for an all-ages audience | The hero headline treatment in all three references |
| `tokens/spacing.json` | 8px scale + tap-target minimums bumped for elderly usability | N/A — accessibility requirement from CLAUDE.md, not the references |
| `tokens/motifs.json` | Descriptive briefs for 6 illustration motifs (Phase 4 builds the actual SVGs) | The everyday-India subject matter (signboards, katori, chai glass) |

## Known gaps (flagged for review)

- **No Google Font matches Yatra One's hand-painted-signboard character
  for Kannada.** `typography.json` picks Baloo Tamma 2 as the warmest
  available option, but it reads as rounded/friendly, not brush-painted.
  Worth revisiting if a closer match turns up, or commissioning one.
- **Dark mode is not addressed.** The reference images include a
  night-highway scene (हॉर्न ओके प्लीज़) that suggests DalGains could
  reasonably want a dusk/dark palette variant, but nothing in the Phase 3
  brief asked for one, so `colors.json` defines a single palette only.
