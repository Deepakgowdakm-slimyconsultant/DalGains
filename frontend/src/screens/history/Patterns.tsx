import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { SpiceChip } from "../../components/SpiceChip";
import { getCurrentUserId } from "../../lib/currentUser";
import { useHistoryData } from "./useHistoryData";
import { EmptyHistoryState } from "./EmptyHistoryState";
import { PieChart } from "./PieChart";
import type { ChartToken } from "./charts";
import type { components } from "../../api/schema.gen";

type MealLog = components["schemas"]["MealLog"];

type RangeKey = "30" | "90" | "all";
const RANGES: RangeKey[] = ["30", "90", "all"];

const PROTEIN_SOURCE_KEYWORDS: { label: string; token: ChartToken; test: RegExp }[] = [
  { label: "Dal", token: "accent_action", test: /\bdal\b/i },
  { label: "Curd / paneer / dairy", token: "accent_success", test: /curd|paneer|yog(h)?urt|milk|dairy|lassi|buttermilk/i },
  { label: "Eggs", token: "accent_celebration", test: /\begg/i },
  { label: "Meat / fish", token: "accent_warning", test: /chicken|mutton|fish|meat|prawn|egg curry/i },
];

function isoWeek(dateStr: string): string {
  const d = new Date(dateStr);
  const day = (d.getUTCDay() + 6) % 7; // Monday = 0
  d.setUTCDate(d.getUTCDate() - day);
  return d.toISOString().slice(0, 10);
}

function SectionHeading({ children }: { children: string }) {
  return <h2 className="mb-sm text-headline font-display-latin text-ink_body">{children}</h2>;
}

export function Patterns() {
  const { t } = useTranslation();
  const userId = getCurrentUserId()!;
  const { profile, plan, logs, loading, entryLabel } = useHistoryData(userId);
  const [range, setRange] = useState<RangeKey>("30");

  const windowed = useMemo(() => {
    const ascending = [...logs].sort((a, b) => a.log_id.localeCompare(b.log_id));
    if (range === "all") return ascending;
    const n = range === "30" ? 30 : 90;
    return ascending.slice(-n);
  }, [logs, range]);

  const mostLogged = useMemo(() => {
    const counts = new Map<string, number>();
    for (const log of windowed) {
      for (const entry of log.entries) {
        const label = entryLabel(entry);
        counts.set(label, (counts.get(label) ?? 0) + 1);
      }
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
  }, [windowed, entryLabel]);

  const proteinSources = useMemo(() => {
    const totals = PROTEIN_SOURCE_KEYWORDS.map((k) => ({ ...k, value: 0 }));
    for (const log of windowed) {
      for (const entry of log.entries) {
        const label = entryLabel(entry);
        const match = totals.find((k) => k.test.test(label));
        if (match) match.value += 1;
      }
    }
    return totals.filter((k) => k.value > 0);
  }, [windowed, entryLabel]);

  const beverageDayStat = useMemo(() => {
    const daysWithBeverageInfo = windowed.filter((l) => l.computed_totals.energy_kcal > 0);
    if (daysWithBeverageInfo.length === 0) return null;
    // Without a per-entry kcal breakdown, approximate using entries whose
    // resolved name matches common beverage words -- an honest
    // simplification, not a true per-entry kcal split.
    const beverageWords = /chai|coffee|tea|lassi|juice|shake|buttermilk|nimbu|beer|wine|whisky|rum|vodka|gin/i;
    let flaggedDays = 0;
    for (const log of daysWithBeverageInfo) {
      if (log.entries.some((e) => beverageWords.test(entryLabel(e)))) flaggedDays += 1;
    }
    return Math.round((100 * flaggedDays) / daysWithBeverageInfo.length);
  }, [windowed, entryLabel]);

  const fastingAdherence = useMemo(() => {
    if (!profile || profile.fasting_protocol === "none") return null;
    const allEntries = windowed.flatMap((l) => l.entries);
    if (allEntries.length === 0) return null;
    const inside = allEntries.filter((e) => !e.outside_eating_window).length;
    return Math.round((100 * inside) / allEntries.length);
  }, [windowed, profile]);

  const weekCallouts = useMemo(() => {
    if (!plan) return null;
    const byWeek = new Map<string, MealLog[]>();
    for (const log of windowed) {
      const week = isoWeek(log.log_id);
      byWeek.set(week, [...(byWeek.get(week) ?? []), log]);
    }
    const weekStats = [...byWeek.entries()]
      .filter(([, weekLogs]) => weekLogs.length >= 3)
      .map(([week, weekLogs]) => {
        const avgAdherence =
          weekLogs.reduce((sum, l) => sum + Math.max(0, 100 * (1 - Math.abs(l.computed_totals.energy_kcal - plan.daily_kcal) / plan.daily_kcal)), 0) /
          weekLogs.length;
        return { week, avgAdherence };
      });
    if (weekStats.length === 0) return null;
    const best = weekStats.reduce((a, b) => (b.avgAdherence > a.avgAdherence ? b : a));
    const toughest = weekStats.reduce((a, b) => (b.avgAdherence < a.avgAdherence ? b : a));
    return { best, toughest };
  }, [windowed, plan]);

  if (loading) return <p className="text-body text-ink_body">{t("weekly.loading")}</p>;
  if (logs.length === 0) return <EmptyHistoryState />;

  return (
    <div className="flex flex-col gap-lg">
      <div className="flex gap-sm">
        {RANGES.map((key) => (
          <SpiceChip key={key} label={t(`history.range_${key}`)} selected={range === key} onClick={() => setRange(key)} />
        ))}
      </div>

      <section>
        <SectionHeading>{t("history.most_logged")}</SectionHeading>
        <div className="flex flex-col gap-xs rounded-md bg-surface_primary p-md">
          {mostLogged.map(([label, count], idx) => (
            <div key={label} className="flex items-center justify-between text-body text-ink_body">
              <span>{idx + 1}. {label}</span>
              <span className="text-caption text-ink_body/70">{t("history.times_logged", { count })}</span>
            </div>
          ))}
        </div>
      </section>

      {proteinSources.length > 0 && (
        <section>
          <SectionHeading>{t("history.protein_sources")}</SectionHeading>
          <div className="rounded-md bg-surface_primary p-md">
            <PieChart slices={proteinSources} />
          </div>
        </section>
      )}

      {beverageDayStat !== null && (
        <section>
          <SectionHeading>{t("history.beverage_day")}</SectionHeading>
          <div className="rounded-md bg-surface_signboard p-lg text-center">
            <p className="text-hero font-display-latin text-ink_hero">{beverageDayStat}%</p>
            <p className="mt-xs text-caption text-ink_hero/80">{t("history.beverage_day_note")}</p>
          </div>
        </section>
      )}

      {fastingAdherence !== null && (
        <section>
          <SectionHeading>{t("history.fasting_adherence")}</SectionHeading>
          <div className="rounded-md bg-surface_signboard p-lg text-center">
            <p className="text-hero font-display-latin text-ink_hero">{fastingAdherence}%</p>
            <p className="mt-xs text-caption text-ink_hero/80">{t("history.fasting_adherence_note")}</p>
          </div>
        </section>
      )}

      {weekCallouts && (
        <section>
          <SectionHeading>{t("history.week_callouts")}</SectionHeading>
          <div className="flex flex-col gap-sm">
            <div className="rounded-md bg-surface_primary p-md">
              <p className="text-body font-medium text-ink_body">{t("history.best_week")}</p>
              <p className="text-caption text-ink_body/70">{t("history.week_of", { date: weekCallouts.best.week })} -- {Math.round(weekCallouts.best.avgAdherence)}%</p>
            </div>
            <div className="rounded-md bg-surface_primary p-md">
              <p className="text-body font-medium text-ink_body">{t("history.toughest_week")}</p>
              <p className="text-caption text-ink_body/70">{t("history.week_of", { date: weekCallouts.toughest.week })} -- {Math.round(weekCallouts.toughest.avgAdherence)}%</p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
