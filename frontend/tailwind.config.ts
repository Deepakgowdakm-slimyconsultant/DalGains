import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import type { Config } from "tailwindcss";

// Tailwind reads the design tokens directly from design/tokens/*.json --
// no hand-tuned Tailwind defaults, no one-off hex codes anywhere else in
// the frontend. Adding a color/spacing/font value means editing the JSON,
// not this file. Loaded via readFileSync (not a static import) so this
// file doesn't need to sit inside a tsconfig "include" that would also
// need to cover design/ for rootDir purposes.
const tokensDir = fileURLToPath(new URL("../design/tokens", import.meta.url));
const readJson = (name: string) => JSON.parse(readFileSync(`${tokensDir}/${name}`, "utf-8"));

const colors = readJson("colors.json");
const typography = readJson("typography.json");
const spacing = readJson("spacing.json");

const paletteColors: Record<string, string> = Object.fromEntries(
  Object.entries(colors.palette as Record<string, { hex: string }>).map(([name, { hex }]) => [name, hex])
);

const semanticColors: Record<string, string> = Object.fromEntries(
  Object.entries(colors.semantic as Record<string, { token: string }>).map(([name, { token }]) => [
    name,
    paletteColors[token],
  ])
);

// Dark-mode semantic overrides live under colors.json's "semantic_dark" key
// (added in Part E). Until then this is an empty object and dark: variants
// simply fall back to the light semantic value.
const semanticDark: Record<string, { token: string }> = colors.semantic_dark ?? {};
const semanticColorsDark: Record<string, string> = Object.fromEntries(
  Object.entries(semanticDark).map(([name, { token }]) => [name, paletteColors[token] ?? token])
);

const spacingScale: Record<string, string> = Object.fromEntries(
  Object.entries(spacing.scale_px as Record<string, number>).map(([name, px]) => [name, `${px}px`])
);

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ...paletteColors,
        ...semanticColors,
        dark: semanticColorsDark,
      },
      spacing: spacingScale,
      maxWidth: {
        app: "480px",
      },
      minWidth: {
        "tap-min": `${spacing.tap_targets.minimum_px.width}px`,
        "tap-primary": `${spacing.tap_targets.primary_action_px.width}px`,
      },
      minHeight: {
        "tap-min": `${spacing.tap_targets.minimum_px.height}px`,
        "tap-primary": `${spacing.tap_targets.primary_action_px.height}px`,
      },
      fontFamily: {
        "display-latin": [typography.families.latin_display.primary, "serif"],
        "display-deva": [typography.families.devanagari_display.primary, "serif"],
        "display-kn": [typography.families.kannada_display.primary, "sans-serif"],
        body: typography.families.body.family_stack,
      },
      fontSize: {
        hero: [`${typography.scale.hero.size_px_min}px`, { lineHeight: `${typography.scale.hero.line_height}` }],
        display: [
          `${typography.scale.display.size_px_min}px`,
          { lineHeight: `${typography.scale.display.line_height}` },
        ],
        headline: [
          `${typography.scale.headline.size_px_min}px`,
          { lineHeight: `${typography.scale.headline.line_height}` },
        ],
        body: [`${typography.scale.body.size_px_min}px`, { lineHeight: `${typography.scale.body.line_height}` }],
        caption: [
          `${typography.scale.caption.size_px_min}px`,
          { lineHeight: `${typography.scale.caption.line_height}` },
        ],
      },
    },
  },
  plugins: [],
} satisfies Config;
