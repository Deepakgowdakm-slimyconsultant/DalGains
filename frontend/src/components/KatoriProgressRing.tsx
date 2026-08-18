import { ringGeometry } from "../lib/ringMath";

interface KatoriProgressRingProps {
  label: string;
  current: number;
  target: number;
  unit?: string;
  size?: "primary" | "small";
  colorToken?: "accent_action" | "accent_success" | "accent_warning" | "accent_celebration";
}

// Full literal class names, so Tailwind's static content scanner can
// find them -- a template-interpolated class name (`stroke-${x}`) would
// not be picked up by the JIT scan.
const RING_STROKE_CLASS: Record<NonNullable<KatoriProgressRingProps["colorToken"]>, string> = {
  accent_action: "stroke-accent_action",
  accent_success: "stroke-accent_success",
  accent_warning: "stroke-accent_warning",
  accent_celebration: "stroke-accent_celebration",
};

/** A circular "how full is the katori" progress ring -- the calories-vs-
 * target motif on Home, reused smaller for protein/fat/carbs. Colors come
 * exclusively from Tailwind's token-derived stroke- and fill- utilities. */
export function KatoriProgressRing({
  label,
  current,
  target,
  unit,
  size = "small",
  colorToken = "accent_action",
}: KatoriProgressRingProps) {
  const dimension = size === "primary" ? 160 : 72;
  const stroke = size === "primary" ? 14 : 8;
  const radius = dimension / 2 - stroke;
  const { circumference, dashOffset, overTarget } = ringGeometry(current, target, radius);

  return (
    <div
      className="flex flex-col items-center gap-xs"
      role="img"
      aria-label={`${label}: ${Math.round(current)} of ${Math.round(target)}${unit ?? ""}`}
    >
      <svg width={dimension} height={dimension} viewBox={`0 0 ${dimension} ${dimension}`} aria-hidden="true">
        <circle
          cx={dimension / 2}
          cy={dimension / 2}
          r={radius}
          fill="none"
          className="stroke-tamarind_brown/15"
          strokeWidth={stroke}
        />
        <circle
          cx={dimension / 2}
          cy={dimension / 2}
          r={radius}
          fill="none"
          className={overTarget ? RING_STROKE_CLASS.accent_warning : RING_STROKE_CLASS[colorToken]}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${dimension / 2} ${dimension / 2})`}
        />
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="central"
          className={size === "primary" ? "fill-ink_body text-headline font-semibold" : "fill-ink_body text-caption"}
        >
          {Math.round(current)}
        </text>
      </svg>
      <span className="text-caption text-ink_body/70">{label}</span>
    </div>
  );
}
