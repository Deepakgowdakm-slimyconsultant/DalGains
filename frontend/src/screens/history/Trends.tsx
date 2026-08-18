import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { SpiceChip } from "../../components/SpiceChip";
import { getCurrentUserId } from "../../lib/currentUser";
import { api } from "../../api/client";
import { useHistoryData } from "./useHistoryData";
import { EmptyHistoryState } from "./EmptyHistoryState";
import { LineSeriesChart, BarChart, type ChartToken } from "./charts";

type RangeKey = "30" | "90" | "all";
const RANGES: RangeKey[] = ["30", "90", "all"];

// Literal legend-dot classes per token, matching charts.tsx's TOKEN_CLASSES.
const LEGEND_DOT_CLASS: Record<ChartToken, string> = {
  accent_action: "bg-accent_action",
  accent_success: "bg-accent_success",
  accent_celebration: "bg-accent_celebration",
  accent_warning: "bg-accent_warning",
  tamarind_brown: "bg-tamarind_brown",
};

function adherenceToken(pct: number): ChartToken {
  if (pct >= 90) return "accent_success";
  if (pct >= 70) return "accent_celebration";
  return "accent_warning";
}

function SectionHeading({ children }: { children: string }) {
  return <h2 className="mb-sm text-headline font-display-latin text-ink_body">{children}</h2>;
}

function Legend({ items }: { items: { label: string; dotClass: string }[] }) {
  return (
    <div className="mt-sm flex flex-wrap gap-md">
      {items.map((item) => (
        <span key={item.label} className="flex items-center gap-xs text-caption text-ink_body/70">
          <span className={`h-2.5 w-2.5 rounded-full ${item.dotClass}`} aria-hidden="true" />
          {item.label}
        </span>
      ))}
    </div>
  );
}

export function Trends() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const userId = getCurrentUserId()!;
  const { plan, logs, loading } = useHistoryData(userId);
  const [range, setRange] = useState<RangeKey>("30");
  const [weightLog, setWeightLog] = useState<Record<string, number>>({});

  useEffect(() => {
    api.GET("/profile/{user_id}/weight", { params: { path: { user_id: userId } } }).then(({ data }) => data && setWeightLog(data));
  }, [userId]);

  const windowed = useMemo(() => {
    const ascending = [...logs].sort((a, b) => a.log_id.localeCompare(b.log_id));
    if (range === "all") return ascending;
    const n = range === "30" ? 30 : 90;
    return ascending.slice(-n);
  }, [logs, range]);

  function jumpToDay(date: string) {
    navigate(`/history/timeline?date=${date}`);
  }

  if (loading) return <p className="text-body text-ink_body">{t("weekly.loading")}</p>;
  if (logs.length === 0) return <EmptyHistoryState />;

  const kcalPoints = windowed.map((l) => ({ x: l.log_id, y: l.computed_totals.energy_kcal }));
  const macroSeries: { label: string; token: ChartToken; points: { x: string; y: number }[] }[] = [
    { label: t("logging.preview_protein"), token: "accent_success", points: windowed.map((l) => ({ x: l.log_id, y: l.computed_totals.protein_g })) },
    { label: t("logging.preview_fat"), token: "accent_celebration", points: windowed.map((l) => ({ x: l.log_id, y: l.computed_totals.fat_g })) },
    { label: t("logging.preview_carbs"), token: "accent_action", points: windowed.map((l) => ({ x: l.log_id, y: l.computed_totals.carbs_g })) },
    { label: t("history.fiber"), token: "tamarind_brown", points: windowed.map((l) => ({ x: l.log_id, y: l.computed_totals.fiber_g })) },
  ];
  const adherenceBars = plan
    ? windowed.map((l) => {
        const pct = 100 * (1 - Math.abs(l.computed_totals.energy_kcal - plan.daily_kcal) / plan.daily_kcal);
        const clamped = Math.max(0, pct);
        return { x: l.log_id, y: clamped, token: adherenceToken(clamped) };
      })
    : [];
  const weightPoints = Object.entries(weightLog)
    .sort(([a], [b]) => a.localeCompare(b))
    .filter(([date]) => windowed.some((l) => l.log_id === date) || range === "all")
    .map(([date, kg]) => ({ x: date, y: kg }));

  return (
    <div className="flex flex-col gap-lg">
      <div className="flex gap-sm">
        {RANGES.map((key) => (
          <SpiceChip key={key} label={t(`history.range_${key}`)} selected={range === key} onClick={() => setRange(key)} />
        ))}
      </div>

      <section>
        <SectionHeading>{t("history.chart_kcal")}</SectionHeading>
        <div className="rounded-md bg-surface_primary p-md">
          <LineSeriesChart
            series={[{ label: "kcal", token: "accent_action", points: kcalPoints }]}
            targetBand={plan ? { min: plan.daily_kcal * 0.9, max: plan.daily_kcal * 1.1 } : null}
            onPointClick={jumpToDay}
          />
          <Legend items={[{ label: t("logging.preview_kcal"), dotClass: "bg-accent_action" }, { label: t("history.target_band"), dotClass: "bg-accent_success/40" }]} />
        </div>
      </section>

      <section>
        <SectionHeading>{t("history.chart_macros")}</SectionHeading>
        <div className="rounded-md bg-surface_primary p-md">
          <LineSeriesChart series={macroSeries} onPointClick={jumpToDay} />
          <Legend items={macroSeries.map((s) => ({ label: s.label, dotClass: LEGEND_DOT_CLASS[s.token] }))} />
        </div>
      </section>

      {plan && (
        <section>
          <SectionHeading>{t("history.chart_adherence")}</SectionHeading>
          <div className="rounded-md bg-surface_primary p-md">
            <BarChart bars={adherenceBars} onBarClick={jumpToDay} />
          </div>
        </section>
      )}

      {weightPoints.length > 0 && (
        <section>
          <SectionHeading>{t("history.chart_weight")}</SectionHeading>
          <div className="rounded-md bg-surface_primary p-md">
            <LineSeriesChart series={[{ label: "kg", token: "accent_warning", points: weightPoints }]} onPointClick={jumpToDay} />
          </div>
        </section>
      )}
    </div>
  );
}
