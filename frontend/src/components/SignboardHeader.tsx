import type { ReactNode } from "react";

interface SignboardHeaderProps {
  title: string;
  subtitle?: string;
  trailing?: ReactNode;
}

/** A painted-signboard-style section header: a colored panel with a
 * display-font headline, used to open every screen and major section. */
export function SignboardHeader({ title, subtitle, trailing }: SignboardHeaderProps) {
  return (
    <header className="flex items-center justify-between gap-md rounded-md bg-surface_signboard px-md py-lg">
      <div className="min-w-0">
        <h1 className="truncate font-display-latin text-display text-ink_hero">{title}</h1>
        {subtitle && <p className="mt-xs text-body text-ink_hero/80">{subtitle}</p>}
      </div>
      {trailing && <div className="shrink-0">{trailing}</div>}
    </header>
  );
}
