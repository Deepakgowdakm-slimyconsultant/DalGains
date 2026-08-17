import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { SpiceChip } from "../../components/SpiceChip";
import { ThaliCard } from "../../components/ThaliCard";
import { DhabaButton } from "../../components/DhabaButton";
import { getCurrentUserId } from "../../lib/currentUser";
import { useHistoryData } from "./useHistoryData";
import { EmptyHistoryState } from "./EmptyHistoryState";
import type { components } from "../../api/schema.gen";

type MealLog = components["schemas"]["MealLog"];

const ADHERENCE_TOLERANCE = 0.1;
const PAGE_SIZE = 20;

type FilterKey = "high_protein" | "over_target" | "under_target" | "on_target" | "festival_days" | "fasting_days" | "beverages_only";
const FILTERS: FilterKey[] = ["high_protein", "over_target", "under_target", "on_target", "festival_days", "fasting_days", "beverages_only"];

function dayLabel(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
}

// Literal classes for the adherence dot -- see KatoriProgressRing's note
// on why Tailwind needs full class strings, not interpolated ones.
function adherenceDotClass(kcal: number, target: number | null): string {
  if (!target) return "bg-tamarind_brown/40";
  if (kcal > target * (1 + ADHERENCE_TOLERANCE)) return "bg-accent_warning";
  if (kcal < target * (1 - ADHERENCE_TOLERANCE)) return "bg-accent_celebration";
  return "bg-accent_success";
}

export function Timeline() {
  const { t } = useTranslation();
  const userId = getCurrentUserId()!;
  const { profile, plan, logs, loading, entryLabel, dayIsBeveragesOnly } = useHistoryData(userId);
  const [activeFilter, setActiveFilter] = useState<FilterKey | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  function matchesFilter(log: MealLog): boolean {
    if (!activeFilter) return true;
    const target = plan?.daily_kcal ?? null;
    switch (activeFilter) {
      case "high_protein":
        return plan ? log.computed_totals.protein_g >= plan.protein_g : false;
      case "over_target":
        return target !== null && log.computed_totals.energy_kcal > target * (1 + ADHERENCE_TOLERANCE);
      case "under_target":
        return target !== null && log.computed_totals.energy_kcal < target * (1 - ADHERENCE_TOLERANCE);
      case "on_target":
        return (
          target !== null &&
          log.computed_totals.energy_kcal >= target * (1 - ADHERENCE_TOLERANCE) &&
          log.computed_totals.energy_kcal <= target * (1 + ADHERENCE_TOLERANCE)
        );
      case "festival_days":
        return log.tags.length > 0;
      case "fasting_days":
        return (
          !!profile &&
          profile.fasting_protocol !== "none" &&
          log.entries.length > 0 &&
          log.entries.every((e) => !e.outside_eating_window)
        );
      case "beverages_only":
        return dayIsBeveragesOnly(log);
    }
  }

  const filtered = useMemo(() => logs.filter(matchesFilter), [logs, activeFilter, profile, plan]);
  const visible = filtered.slice(0, visibleCount);

  function toggleExpanded(logId: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(logId)) next.delete(logId);
      else next.add(logId);
      return next;
    });
  }

  if (loading) return <p className="text-body text-ink_body">{t("weekly.loading")}</p>;
  if (logs.length === 0) return <EmptyHistoryState />;

  return (
    <div className="flex flex-col gap-md">
      <div className="flex flex-wrap gap-sm">
        {FILTERS.map((key) => (
          <SpiceChip
            key={key}
            label={t(`history.filter.${key}`)}
            selected={activeFilter === key}
            onClick={() => setActiveFilter((cur) => (cur === key ? null : key))}
          />
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-body text-ink_body/70">{t("history.no_matching_days")}</p>
      ) : (
        <>
          <div className="flex flex-col gap-sm">
            {visible.map((log) => {
              const isExpanded = expanded.has(log.log_id);
              return (
                <div key={log.log_id} className="rounded-md bg-surface_primary p-md">
                  <button type="button" onClick={() => toggleExpanded(log.log_id)} className="flex w-full items-center justify-between gap-sm text-left">
                    <span className="flex items-center gap-sm">
                      <span className={`h-3 w-3 shrink-0 rounded-full ${adherenceDotClass(log.computed_totals.energy_kcal, plan?.daily_kcal ?? null)}`} aria-hidden="true" />
                      <span className="text-body font-medium text-ink_body">{dayLabel(log.log_id)}</span>
                    </span>
                    <span className="text-caption text-ink_body/70">
                      {Math.round(log.computed_totals.energy_kcal)} kcal · {log.entries.length}
                    </span>
                  </button>
                  {isExpanded && (
                    <div className="mt-sm flex flex-col gap-xs">
                      {log.entries.map((entry, idx) => (
                        <ThaliCard key={idx} title={entryLabel(entry)} meta={`${entry.qty} ${entry.unit}`} />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          {visibleCount < filtered.length && (
            <DhabaButton variant="secondary" onClick={() => setVisibleCount((c) => c + PAGE_SIZE)} className="w-full">
              {t("history.load_more")}
            </DhabaButton>
          )}
        </>
      )}
    </div>
  );
}
