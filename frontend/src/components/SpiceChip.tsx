interface SpiceChipProps {
  label: string;
  selected?: boolean;
  onClick?: () => void;
}

/** A small pill-shaped tag -- insight kind labels, filter chips on
 * History, suggested-action chips on Insights. */
export function SpiceChip({ label, selected = false, onClick }: SpiceChipProps) {
  const Tag = onClick ? "button" : "span";
  return (
    <Tag
      type={onClick ? "button" : undefined}
      onClick={onClick}
      aria-pressed={onClick ? selected : undefined}
      className={
        "inline-flex min-h-tap-min items-center rounded-full border px-md text-caption font-medium " +
        (selected
          ? "border-accent_action bg-accent_action text-signboard_white"
          : "border-tamarind_brown/30 bg-transparent text-ink_body")
      }
    >
      {label}
    </Tag>
  );
}
