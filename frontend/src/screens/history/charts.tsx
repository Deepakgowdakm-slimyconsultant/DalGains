// Hand-rolled SVG charts -- deliberately not a charting library. Keeps
// every color on the design-token palette with zero risk of a library's
// default series colors leaking in, and this is the only place in the
// frontend that needs charts. Library choice flagged for review in the
// Phase 4 report.

export type ChartToken = "accent_action" | "accent_success" | "accent_celebration" | "accent_warning" | "tamarind_brown";

// Full literal class strings per token -- Tailwind's static scanner
// can't follow a derived/interpolated class name (same reasoning as
// KatoriProgressRing's RING_STROKE_CLASS).
const TOKEN_CLASSES: Record<ChartToken, { stroke: string; fill: string }> = {
  accent_action: { stroke: "stroke-accent_action", fill: "fill-accent_action" },
  accent_success: { stroke: "stroke-accent_success", fill: "fill-accent_success" },
  accent_celebration: { stroke: "stroke-accent_celebration", fill: "fill-accent_celebration" },
  accent_warning: { stroke: "stroke-accent_warning", fill: "fill-accent_warning" },
  tamarind_brown: { stroke: "stroke-tamarind_brown", fill: "fill-tamarind_brown" },
};

export interface Point {
  x: string; // date, YYYY-MM-DD
  y: number;
}

interface LineSeriesChartProps {
  series: { points: Point[]; token: ChartToken; label: string }[];
  height?: number;
  targetBand?: { min: number; max: number } | null;
  onPointClick?: (date: string) => void;
}

const CHART_WIDTH = 320;

function scale(values: number[], height: number, padding: number) {
  const min = Math.min(0, ...values);
  const max = Math.max(1, ...values);
  return (v: number) => height - padding - ((v - min) / (max - min || 1)) * (height - padding * 2);
}

/** Multi-line chart (kcal over time, or protein/fat/carbs/fiber
 * together) with an optional shaded target band. All series share one
 * x-axis (dates); points are evenly spaced regardless of gaps, since a
 * personal food log has more meaning day-to-day than in true time
 * spacing. */
export function LineSeriesChart({ series, height = 160, targetBand, onPointClick }: LineSeriesChartProps) {
  const allDates = series[0]?.points.map((p) => p.x) ?? [];
  const allValues = series.flatMap((s) => s.points.map((p) => p.y));
  const padding = 12;
  const y = scale(targetBand ? [...allValues, targetBand.min, targetBand.max] : allValues, height, padding);
  const stepX = allDates.length > 1 ? (CHART_WIDTH - padding * 2) / (allDates.length - 1) : 0;
  const x = (i: number) => padding + i * stepX;

  return (
    <svg viewBox={`0 0 ${CHART_WIDTH} ${height}`} width="100%" height={height} role="img" aria-label="Trend chart">
      {targetBand && (
        <rect
          x={padding}
          y={y(targetBand.max)}
          width={CHART_WIDTH - padding * 2}
          height={Math.max(0, y(targetBand.min) - y(targetBand.max))}
          className="fill-accent_success/15"
        />
      )}
      <line x1={padding} y1={height - padding} x2={CHART_WIDTH - padding} y2={height - padding} className="stroke-tamarind_brown/30" strokeWidth={1} />
      {series.map((s) => (
        <polyline
          key={s.label}
          fill="none"
          className={TOKEN_CLASSES[s.token].stroke}
          strokeWidth={2}
          points={s.points.map((p, i) => `${x(i)},${y(p.y)}`).join(" ")}
        />
      ))}
      {series.map((s) =>
        s.points.map((p, i) => (
          <circle
            key={`${s.label}-${p.x}`}
            cx={x(i)}
            cy={y(p.y)}
            r={onPointClick ? 6 : 3}
            stroke="none"
            className={`${TOKEN_CLASSES[s.token].fill} ${onPointClick ? "cursor-pointer" : ""}`}
            onClick={onPointClick ? () => onPointClick(p.x) : undefined}
          >
            <title>{`${p.x}: ${Math.round(p.y)}`}</title>
          </circle>
        ))
      )}
    </svg>
  );
}

interface BarChartProps {
  bars: { x: string; y: number; token: ChartToken }[];
  height?: number;
  onBarClick?: (date: string) => void;
}

/** Bar chart (adherence%), each bar colored independently by band. */
export function BarChart({ bars, height = 120, onBarClick }: BarChartProps) {
  const padding = 12;
  const max = Math.max(100, ...bars.map((b) => b.y));
  const barWidth = bars.length > 0 ? (CHART_WIDTH - padding * 2) / bars.length : 0;

  return (
    <svg viewBox={`0 0 ${CHART_WIDTH} ${height}`} width="100%" height={height} role="img" aria-label="Adherence chart">
      <line x1={padding} y1={height - padding} x2={CHART_WIDTH - padding} y2={height - padding} className="stroke-tamarind_brown/30" strokeWidth={1} />
      {bars.map((b, i) => {
        const barHeight = ((height - padding * 2) * b.y) / max;
        return (
          <rect
            key={b.x}
            x={padding + i * barWidth + 1}
            y={height - padding - barHeight}
            width={Math.max(1, barWidth - 2)}
            height={barHeight}
            className={`${TOKEN_CLASSES[b.token].fill} ${onBarClick ? "cursor-pointer" : ""}`}
            onClick={onBarClick ? () => onBarClick(b.x) : undefined}
          >
            <title>{`${b.x}: ${Math.round(b.y)}%`}</title>
          </rect>
        );
      })}
    </svg>
  );
}
