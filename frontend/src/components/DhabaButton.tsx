import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

interface DhabaButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

// Full literal class strings per variant -- required so Tailwind's static
// scanner picks them up (a template-interpolated class name is invisible
// to the JIT content scan).
//
// primary's text is coal_black, not signboard_white: white-on-
// saffron_orange only hits 2.77:1, well under WCAG AA's 4.5:1 floor for
// text (design/contrast-report.md) -- dark text on this particular
// orange is what actually passes (5.9:1). secondary's text is
// accent_action_text, not accent_action itself, for the same reason:
// saffron_orange as a small text color against light surfaces is only
// ~2.4:1. danger (chilli_red bg + white text) already passes at 5.5:1,
// so it's unchanged.
const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-accent_action text-coal_black",
  secondary: "bg-transparent text-accent_action_text border-2 border-accent_action",
  danger: "bg-accent_warning text-signboard_white",
};

/** The primary call-to-action button ("Log this", "Confirm portion",
 * etc.) -- always at least the 56x56 primary tap target from
 * design/tokens/spacing.json, never smaller. */
export function DhabaButton({ variant = "primary", className = "", children, ...rest }: DhabaButtonProps) {
  return (
    <button
      type="button"
      className={`min-h-tap-primary min-w-tap-primary rounded-md px-lg text-body font-semibold active:opacity-80 disabled:opacity-40 ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
