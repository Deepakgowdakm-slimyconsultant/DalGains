import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

interface DhabaButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

// Full literal class strings per variant -- required so Tailwind's static
// scanner picks them up (a template-interpolated class name is invisible
// to the JIT content scan).
const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-accent_action text-signboard_white",
  secondary: "bg-transparent text-accent_action border-2 border-accent_action",
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
