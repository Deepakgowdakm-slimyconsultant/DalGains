import type { ChartToken } from "./charts";

const TOKEN_FILL: Record<ChartToken, string> = {
  accent_action: "fill-accent_action",
  accent_success: "fill-accent_success",
  accent_celebration: "fill-accent_celebration",
  accent_warning: "fill-accent_warning",
  tamarind_brown: "fill-tamarind_brown",
};

interface Slice {
  label: string;
  value: number;
  token: ChartToken;
}

const SIZE = 140;
const RADIUS = SIZE / 2;

function arcPath(startAngle: number, endAngle: number): string {
  const start = {
    x: RADIUS + RADIUS * Math.cos(startAngle),
    y: RADIUS + RADIUS * Math.sin(startAngle),
  };
  const end = {
    x: RADIUS + RADIUS * Math.cos(endAngle),
    y: RADIUS + RADIUS * Math.sin(endAngle),
  };
  const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
  return `M ${RADIUS} ${RADIUS} L ${start.x} ${start.y} A ${RADIUS} ${RADIUS} 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
}

/** A simple hand-painted-style pie chart -- flat token-colored wedges,
 * no gradients or 3D effects, used for "Your protein sources". */
export function PieChart({ slices }: { slices: Slice[] }) {
  const total = slices.reduce((sum, s) => sum + s.value, 0);
  if (total === 0) return null;

  let angle = -Math.PI / 2;
  // A slice sweeping the full 2*PI (a single 100% slice, or floating-
  // point rounding landing exactly on it) degenerates to a zero-area
  // path -- an SVG arc's start and endpoint would coincide. Clip just
  // under a full turn so it still renders as a (near-)complete circle.
  const FULL_TURN_EPSILON = 0.001;
  const wedges = slices.map((slice) => {
    const rawSweep = (slice.value / total) * Math.PI * 2;
    const sweep = Math.min(rawSweep, Math.PI * 2 - FULL_TURN_EPSILON);
    const path = arcPath(angle, angle + sweep);
    angle += rawSweep;
    return { ...slice, path };
  });

  return (
    <div className="flex flex-col items-center gap-md">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width={SIZE} height={SIZE} role="img" aria-label="Protein sources breakdown">
        {wedges.map((w) => (
          <path key={w.label} d={w.path} className={`${TOKEN_FILL[w.token]} stroke-dhaba_cream`} strokeWidth={1}>
            <title>{`${w.label}: ${Math.round((w.value / total) * 100)}%`}</title>
          </path>
        ))}
      </svg>
      <ul className="flex flex-wrap justify-center gap-md">
        {slices.map((s) => (
          <li key={s.label} className="flex items-center gap-xs text-caption text-ink_body/80">
            <span className={`h-2.5 w-2.5 rounded-full ${TOKEN_FILL[s.token].replace("fill-", "bg-")}`} aria-hidden="true" />
            {s.label} ({Math.round((s.value / total) * 100)}%)
          </li>
        ))}
      </ul>
    </div>
  );
}
