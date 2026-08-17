interface SpiceChipProps {
  label: string;
  selected?: boolean;
  onClick?: () => void;
  /** 'light' (default) for chips on light surfaces (surface_primary,
   * signboard_white); 'dark' for chips placed on a dark signboard-colored
   * card (surface_signboard) -- ink_body-on-tamarind_brown is otherwise
   * near-illegible. */
  tone?: "light" | "dark";
}

// Full literal class strings per (tone, selected) combination -- required
// so Tailwind's static scanner can see them (see KatoriProgressRing's
// note on template-interpolated class names not being detected).
const TONE_CLASSES: Record<"light" | "dark", { selected: string; unselected: string }> = {
  light: {
    selected: "border-accent_action bg-accent_action text-signboard_white",
    unselected: "border-tamarind_brown/30 bg-transparent text-ink_body",
  },
  dark: {
    selected: "border-signboard_white bg-signboard_white text-tamarind_brown",
    unselected: "border-ink_hero/50 bg-transparent text-ink_hero",
  },
};

/** A small pill-shaped tag -- insight kind labels, filter chips on
 * History, suggested-action chips on Insights. */
export function SpiceChip({ label, selected = false, onClick, tone = "light" }: SpiceChipProps) {
  const Tag = onClick ? "button" : "span";
  const classes = TONE_CLASSES[tone];
  return (
    <Tag
      type={onClick ? "button" : undefined}
      onClick={onClick}
      aria-pressed={onClick ? selected : undefined}
      className={
        "inline-flex min-h-tap-min items-center rounded-full border px-md text-caption font-medium " +
        (selected ? classes.selected : classes.unselected)
      }
    >
      {label}
    </Tag>
  );
}
