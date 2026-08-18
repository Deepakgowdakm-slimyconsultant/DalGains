import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { SpiceChip } from "../../components/SpiceChip";
import { getCurrentUserId } from "../../lib/currentUser";
import { api } from "../../api/client";
import { useHistoryData } from "./useHistoryData";
import { EmptyHistoryState } from "./EmptyHistoryState";
import { PieChart } from "./PieChart";
import type { ChartToken } from "./charts";
import type { components } from "../../api/schema.gen";

type MealLog = components["schemas"]["MealLog"];
type CategoryBreakdown = components["schemas"]["CategoryBreakdown"];

type RangeKey = "30" | "90" | "all";
const RANGES: RangeKey[] = ["30", "90", "all"];

// Display label per Ingredient.category (src/core/schemas.py's
// IngredientCategory) for the protein-sources pie. Categories not
// listed here fall back to a title-cased version of the raw key, and
// only the top 4 by actual protein grams get their own slice -- the
// rest are pooled into "Other" so the chart stays readable.
const CATEGORY_LABELS: Record<string, string> = {
  dal: "Dal",
  dairy: "Dairy",
  egg: "Eggs",
  meat: "Meat",
  fish: "Fish",
  nut_seed: "Nuts & seeds",
  grain: "Grains",
  vegetable: "Vegetables",
  fruit: "Fruit",
  oil_fat: "Oil / ghee",
  beverage_base: "Beverages",
  sweetener: "Sweeteners",
  spice: "Spices",
  prepared: "Prepared foods",
  other: "Other",
};

const PIE_TOKENS: ChartToken[] = ["accent_action", "accent_success", "accent_celebration", "accent_warning", "tamarind_brown"];

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
  const [breakdown, setBreakdown] = useState<CategoryBreakdown | null>(null);

  const windowed = useMemo(() => {
    const ascending = [...logs].sort((a, b) => a.log_id.localeCompare(b.log_id));
    if (range === "all") return ascending;
    const n = range === "30" ? 30 : 90;
    return ascending.slice(-n);
  }, [logs, range]);

  const startDate = windowed[0]?.log_id;
  const endDate = windowed[windowed.length - 1]?.log_id;

  useEffect(() => {
    if (!startDate || !endDate) {
      setBreakdown(null);
      return;
    }
    api
      .GET("/logs/{user_id}/category_breakdown/{start}/{end}", {
        params: { path: { user_id: userId, start: startDate, end: endDate } },
      })
      .then(({ data }) => data && setBreakdown(data));
  }, [userId, startDate, endDate]);

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

  // True gram-level attribution from GET .../category_breakdown, not a
  // name-match on the entry's display label -- a recipe's protein is
  // split ingredient-by-ingredient server-side (src.logging.
  // category_breakdown), the same way compute_nutrition itself scales
  // each RecipeIngredient.
  const proteinSources = useMemo(() => {
    if (!breakdown) return [];
    const entries = Object.entries(breakdown.by_category)
      .map(([category, totals]) => ({ category, protein_g: totals.protein_g }))
      .filter((c) => c.protein_g > 0)
      .sort((a, b) => b.protein_g - a.protein_g);

    const top = entries.slice(0, 4);
    const restTotal = entries.slice(4).reduce((sum, c) => sum + c.protein_g, 0);
    const slices = top.map((c, i) => ({
      label: CATEGORY_LABELS[c.category] ?? c.category,
      value: c.protein_g,
      token: PIE_TOKENS[i],
    }));
    if (restTotal > 0) slices.push({ label: t("history.other_category"), value: restTotal, token: PIE_TOKENS[4] });
    return slices;
  }, [breakdown, t]);

  // Average of each day's (beverage kcal / total kcal), not a name-match
  // guess -- beverage_kcal_by_date already only counts entries that are
  // either a beverage-builder recipe (meal_type == "beverage") or a raw
  // ingredient with category == "beverage_base".
  const beverageDayStat = useMemo(() => {
    if (!breakdown) return null;
    const days = Object.entries(breakdown.total_kcal_by_date).filter(([, kcal]) => kcal > 0);
    if (days.length === 0) return null;
    const avgPct =
      days.reduce((sum, [date, totalKcal]) => sum + (100 * (breakdown.beverage_kcal_by_date[date] ?? 0)) / totalKcal, 0) / days.length;
    return Math.round(avgPct);
  }, [breakdown]);

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
