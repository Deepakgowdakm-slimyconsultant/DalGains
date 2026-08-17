import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { KatoriProgressRing } from "../components/KatoriProgressRing";
import { ThaliCard } from "../components/ThaliCard";
import { DhabaButton } from "../components/DhabaButton";
import { LogEntryFlow } from "./LogEntryFlow";
import { api } from "../api/client";
import { getCurrentUserId } from "../lib/currentUser";
import type { components } from "../api/schema.gen";

type UserProfile = components["schemas"]["UserProfile"];
type PlanRecommendation = components["schemas"]["PlanRecommendation"];
type MealLog = components["schemas"]["MealLog"];
type Insight = components["schemas"]["Insight"];
type LogEntry = components["schemas"]["LogEntry"];

const INSIGHT_BODY_FIELD = { en: "body_en", hi: "body_hi", kn: "body_kn" } as const;

const DISMISSED_KEY = "dalgains_dismissed_insights";

function loadDismissed(): string[] {
  try {
    return JSON.parse(localStorage.getItem(DISMISSED_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function greetingKey(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "home.greeting_morning";
  if (hour < 17) return "home.greeting_afternoon";
  return "home.greeting_evening";
}

export function Home() {
  const { t, i18n } = useTranslation();
  const userId = getCurrentUserId()!;
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [plan, setPlan] = useState<PlanRecommendation | null>(null);
  const [today, setToday] = useState<MealLog | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [dismissed, setDismissed] = useState<string[]>(loadDismissed());
  const [sheetOpen, setSheetOpen] = useState(false);
  const [entryNames, setEntryNames] = useState<Record<string, string>>({});
  const [todaysWeight, setTodaysWeight] = useState<number | null>(null);
  const [weightInput, setWeightInput] = useState("");
  const [loggingWeight, setLoggingWeight] = useState(false);

  const reload = useCallback(() => {
    api.GET("/profile/{user_id}", { params: { path: { user_id: userId } } }).then(({ data }) => data && setProfile(data));
    api.GET("/profile/{user_id}/plan", { params: { path: { user_id: userId } } }).then(({ data }) => data && setPlan(data));
    api.GET("/logs/{user_id}/day/{date}", { params: { path: { user_id: userId, date: todayIso() } } }).then(({ data }) => {
      if (data && "entries" in data) setToday(data);
      else setToday(null);
    });
    api.GET("/insights/{user_id}", { params: { path: { user_id: userId } } }).then(({ data }) => data && setInsights(data));
    api.GET("/profile/{user_id}/weight", { params: { path: { user_id: userId } } }).then(({ data }) => {
      setTodaysWeight(data?.[todayIso()] ?? null);
    });
  }, [userId]);

  async function saveWeight() {
    const kg = Number(weightInput);
    if (!kg || kg <= 0) return;
    setLoggingWeight(true);
    const { data } = await api.POST("/profile/{user_id}/weight", {
      params: { path: { user_id: userId } },
      body: { user_id: userId, date: todayIso(), weight_kg: kg },
    });
    setLoggingWeight(false);
    if (data) setTodaysWeight(data.weight_kg);
  }

  useEffect(() => {
    reload();
  }, [reload]);

  // Entries only carry recipe_id/ingredient_id -- look up display names
  // once per id and cache them, rather than re-fetching on every render.
  useEffect(() => {
    if (!today) return;
    for (const entry of today.entries) {
      const id = entry.recipe_id ?? entry.ingredient_id;
      if (!id || entryNames[id]) continue;
      if (entry.recipe_id) {
        api.GET("/recipes/{recipe_id}", { params: { path: { recipe_id: entry.recipe_id } } }).then(({ data }) => {
          if (data) setEntryNames((names) => ({ ...names, [id]: data.name }));
        });
      } else if (entry.ingredient_id) {
        api.GET("/ingredients/{ingredient_id}", { params: { path: { ingredient_id: entry.ingredient_id } } }).then(({ data }) => {
          if (data) setEntryNames((names) => ({ ...names, [id]: data.name }));
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [today]);

  function dismissInsight(id: string) {
    const next = [...dismissed, id];
    setDismissed(next);
    localStorage.setItem(DISMISSED_KEY, JSON.stringify(next));
  }

  function entryLabel(entry: LogEntry): string {
    const id = entry.recipe_id ?? entry.ingredient_id ?? "";
    return entryNames[id] ?? id;
  }

  function insightBody(insight: Insight): string {
    const field = INSIGHT_BODY_FIELD[i18n.language as keyof typeof INSIGHT_BODY_FIELD] ?? "body_en";
    return insight[field];
  }

  const activeInsight = insights.find((i) => !dismissed.includes(i.insight_id));
  const totals = today?.computed_totals;

  return (
    <div className="flex flex-col gap-lg p-md pb-32">
      <SignboardHeader
        title={profile ? `${t(greetingKey())}, ${profile.name}` : t(greetingKey())}
        subtitle={new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}
      />

      {plan && (
        <div className="flex flex-col items-center gap-md rounded-md bg-surface_primary p-md">
          <KatoriProgressRing label="kcal" current={totals?.energy_kcal ?? 0} target={plan.daily_kcal} size="primary" />
          <div className="flex gap-lg">
            <KatoriProgressRing label={t("plan.protein_target")} current={totals?.protein_g ?? 0} target={plan.protein_g} colorToken="accent_success" />
            <KatoriProgressRing label={t("plan.fat_target")} current={totals?.fat_g ?? 0} target={plan.fat_g} colorToken="accent_celebration" />
            <KatoriProgressRing label={t("plan.carbs_target")} current={totals?.carbs_g ?? 0} target={plan.carbs_g} colorToken="accent_action" />
          </div>
        </div>
      )}

      <div className="flex items-center justify-between gap-sm rounded-md bg-surface_primary p-md">
        {todaysWeight !== null ? (
          <span className="text-body text-ink_body">{t("home.weight_logged_today", { weight: todaysWeight })}</span>
        ) : (
          <>
            <span className="text-body text-ink_body">{t("home.log_weight_prompt")}</span>
            <div className="flex items-center gap-xs">
              <input
                type="number"
                inputMode="decimal"
                value={weightInput}
                onChange={(e) => setWeightInput(e.target.value)}
                placeholder="kg"
                className="min-h-tap-min w-16 rounded-md border-2 border-tamarind_brown/30 bg-signboard_white px-sm text-body text-ink_body"
              />
              <DhabaButton onClick={saveWeight} disabled={loggingWeight}>
                {t("common.save")}
              </DhabaButton>
            </div>
          </>
        )}
      </div>

      {activeInsight && (
        <div className="flex items-start justify-between gap-sm rounded-md bg-surface_signboard p-md">
          <div className="min-w-0">
            <p className="text-body font-semibold text-ink_hero">{activeInsight.title}</p>
            <p className="mt-xs text-caption text-ink_hero/80">{insightBody(activeInsight)}</p>
          </div>
          <button
            type="button"
            onClick={() => dismissInsight(activeInsight.insight_id)}
            aria-label={t("common.done")}
            className="flex min-h-tap-min min-w-tap-min shrink-0 items-center justify-center rounded-full text-headline text-ink_hero"
          >
            &times;
          </button>
        </div>
      )}

      <div>
        <h2 className="mb-sm text-headline font-display-latin text-ink_body">{t("home.today_entries_title")}</h2>
        {today && today.entries.length > 0 ? (
          <div className="flex flex-col gap-xs">
            {today.entries.map((entry, idx) => (
              <ThaliCard
                key={idx}
                title={entryLabel(entry)}
                subtitle={entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" }) : undefined}
                meta={`${entry.qty} ${entry.unit}`}
                icon={<span>{entry.recipe_id ? "🍽️" : "🥕"}</span>}
              />
            ))}
          </div>
        ) : (
          <p className="text-body text-ink_body/70">{t("home.no_entries_yet")}</p>
        )}
      </div>

      <div className="fixed bottom-24 left-1/2 z-40 w-full max-w-app -translate-x-1/2 px-md">
        <DhabaButton onClick={() => setSheetOpen(true)} className="w-full shadow-lg">
          {t("home.log_button")}
        </DhabaButton>
      </div>

      <LogEntryFlow open={sheetOpen} userId={userId} onClose={() => setSheetOpen(false)} onLogged={reload} />
    </div>
  );
}
