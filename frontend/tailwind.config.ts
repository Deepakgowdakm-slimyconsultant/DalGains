import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import type { Config } from "tailwindcss";
import plugin from "tailwindcss/plugin";

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

function hexToRgbTriplet(hex: string): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `${r} ${g} ${b}`;
}

// Semantic tokens (surface_primary, ink_body, accent_action, ...) are the
// ones that change between light and dark mode -- so, unlike the raw
// palette colors above (which stay static hex; a raw palette swatch is
// never itself mode-dependent), they're wired as CSS custom properties.
// One utility class (e.g. `bg-surface_primary`) then works correctly in
// both modes with zero `dark:` prefixing needed anywhere else in the
// frontend -- the actual light/dark values are declared once, below, and
// swapped by the `.dark` class on <html> (src/lib/theme.ts).
const semanticNames = Object.keys(colors.semantic as Record<string, unknown>);
const semanticColors: Record<string, string> = Object.fromEntries(
  semanticNames.map((name) => [name, `rgb(var(--color-${name.replace(/_/g, "-")}) / <alpha-value>)`])
);

function cssVarBlock(source: Record<string, { token: string }>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(source)
      // colors.json's "$note" keys are documentation, not tokens.
      .filter(([name]) => !name.startsWith("$"))
      .map(([name, { token }]) => [`--color-${name.replace(/_/g, "-")}`, hexToRgbTriplet(paletteColors[token] ?? token)])
  );
}

const lightVars = cssVarBlock(colors.semantic);
// Falls back to the light value for any semantic token semantic_dark
// doesn't override, rather than being left undefined.
const darkVars = { ...lightVars, ...cssVarBlock(colors.semantic_dark ?? {}) };

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
  plugins: [
    plugin(({ addBase }) => {
      addBase({
        ":root": lightVars,
        ":root.dark": darkVars,
      });
    }),
  ],
} satisfies Config;
