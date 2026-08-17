import type { ReactNode } from "react";

interface ThaliCardProps {
  title: string;
  subtitle?: string;
  meta?: string;
  icon?: ReactNode;
  onClick?: () => void;
  trailing?: ReactNode;
}

/** A rounded card for one food/recipe/beverage/entry -- used in search
 * results, the log-entry flow, and timeline entries. Named for the thali
 * plate motif: a compact round "serving" of information. */
export function ThaliCard({ title, subtitle, meta, icon, onClick, trailing }: ThaliCardProps) {
  const Tag = onClick ? "button" : "div";
  return (
    <Tag
      onClick={onClick}
      type={onClick ? "button" : undefined}
      className="flex w-full min-h-tap-min items-center gap-md rounded-md border border-tamarind_brown/15 bg-surface_card px-md py-sm text-left"
    >
      {icon && (
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-dhaba_cream text-headline">
          {icon}
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-body font-medium text-ink_body">{title}</span>
        {subtitle && <span className="block truncate text-caption text-ink_body/70">{subtitle}</span>}
      </span>
      {meta && <span className="shrink-0 text-caption text-ink_body/70">{meta}</span>}
      {trailing && <span className="shrink-0">{trailing}</span>}
    </Tag>
  );
}
