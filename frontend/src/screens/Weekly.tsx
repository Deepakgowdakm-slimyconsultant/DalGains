import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { KatoriProgressRing } from "../components/KatoriProgressRing";
import { api } from "../api/client";
import { getCurrentUserId } from "../lib/currentUser";
import type { components } from "../api/schema.gen";

type WeeklySummary = components["schemas"]["WeeklySummary"];

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function dayLabel(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, { weekday: "short" });
}

// Adherence-to-color mapping needs literal class names for Tailwind's
// static scanner (see KatoriProgressRing's RING_STROKE_CLASS comment).
function adherenceColor(pct: number | null): "accent_success" | "accent_celebration" | "accent_warning" {
  if (pct === null) return "accent_celebration";
  if (pct >= 90) return "accent_success";
  if (pct >= 70) return "accent_celebration";
  return "accent_warning";
}

export function Weekly() {
  const { t } = useTranslation();
  const userId = getCurrentUserId()!;
  const [summary, setSummary] = useState<WeeklySummary | null>(null);

  useEffect(() => {
    api.GET("/logs/{user_id}/week/{week_ending}", { params: { path: { user_id: userId, week_ending: todayIso() } } }).then(
      ({ data }) => data && setSummary(data)
    );
  }, [userId]);

  if (!summary) {
    return <div className="p-md text-body text-ink_body">{t("weekly.loading")}</div>;
  }

  const { averages } = summary;

  return (
    <div className="flex flex-col gap-lg p-md pb-32">
      <SignboardHeader title={t("weekly.title")} subtitle={`${summary.week_start_date} - ${summary.week_end_date}`} />

      <div className="flex justify-between gap-xs overflow-x-auto rounded-md bg-surface_primary p-md">
        {summary.days.map((day) => (
          <div key={day.date} className="flex flex-col items-center gap-xs">
            <KatoriProgressRing
              label={dayLabel(day.date)}
              current={day.totals.energy_kcal}
              target={day.target_kcal ?? (day.totals.energy_kcal || 1)}
              colorToken={day.entry_count > 0 ? adherenceColor(day.adherence_pct) : "accent_celebration"}
            />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-md rounded-md bg-surface_signboard p-lg text-center text-ink_hero">
        <div>
          <p className="text-hero font-display-latin">{Math.round(summary.target_adherence_pct)}%</p>
          <p className="text-caption text-ink_hero/80">{t("weekly.adherence")}</p>
        </div>
        <div>
          <p className="text-hero font-display-latin">{summary.streak_days}</p>
          <p className="text-caption text-ink_hero/80">{t("weekly.streak")}</p>
        </div>
      </div>

      <div className="rounded-md bg-surface_primary p-md">
        <h2 className="mb-sm text-headline font-display-latin text-ink_body">{t("weekly.averages")}</h2>
        <div className="grid grid-cols-2 gap-sm text-body text-ink_body">
          <p>{t("logging.preview_kcal")}: {Math.round(averages.energy_kcal)}</p>
          <p>{t("logging.preview_protein")}: {Math.round(averages.protein_g)}g</p>
          <p>{t("logging.preview_fat")}: {Math.round(averages.fat_g)}g</p>
          <p>{t("logging.preview_carbs")}: {Math.round(averages.carbs_g)}g</p>
        </div>
      </div>

      {summary.notable_days.length > 0 && (
        <div>
          <h2 className="mb-sm text-headline font-display-latin text-ink_body">{t("weekly.notable_days")}</h2>
          <ul className="flex flex-col gap-xs">
            {summary.notable_days.map((note) => (
              <li key={note} className="rounded-md bg-surface_primary p-md text-body text-ink_body">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
