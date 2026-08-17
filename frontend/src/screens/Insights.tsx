import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { SpiceChip } from "../components/SpiceChip";
import { LogEntryFlow } from "./LogEntryFlow";
import { api } from "../api/client";
import { getCurrentUserId } from "../lib/currentUser";
import type { components } from "../api/schema.gen";

type Insight = components["schemas"]["Insight"];

const DISMISSED_KEY = "dalgains_dismissed_insights";
const SEVERITY_ORDER: Insight["severity"][] = ["urgent", "warn", "suggest", "info"];
const INSIGHT_BODY_FIELD = { en: "body_en", hi: "body_hi", kn: "body_kn" } as const;

// Literal per-severity classes -- Tailwind's static scanner can't follow
// a template-interpolated class name (see KatoriProgressRing).
const SEVERITY_BADGE_CLASS: Record<Insight["severity"], string> = {
  urgent: "bg-accent_warning text-signboard_white",
  warn: "bg-accent_warning/80 text-signboard_white",
  suggest: "bg-accent_celebration text-ink_body",
  info: "bg-tamarind_brown/15 text-ink_body",
};

function loadDismissed(): string[] {
  try {
    return JSON.parse(localStorage.getItem(DISMISSED_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveDismissed(ids: string[]) {
  localStorage.setItem(DISMISSED_KEY, JSON.stringify(ids));
}

function InsightCard({
  insight,
  bodyField,
  dismissed,
  onDismiss,
  onRestore,
  onSuggestedAction,
}: {
  insight: Insight;
  bodyField: keyof typeof INSIGHT_BODY_FIELD;
  dismissed: boolean;
  onDismiss: () => void;
  onRestore: () => void;
  onSuggestedAction: () => void;
}) {
  const { t } = useTranslation();
  const [showWhy, setShowWhy] = useState(false);
  const body = insight[INSIGHT_BODY_FIELD[bodyField]];
  const evidenceEntries = Object.entries(insight.evidence ?? {});

  return (
    <div className={`rounded-md p-md ${dismissed ? "bg-surface_primary opacity-60" : "bg-surface_signboard"}`}>
      <div className="flex items-start justify-between gap-sm">
        <div className="min-w-0">
          <span className={`inline-block rounded-full px-sm text-caption font-medium ${SEVERITY_BADGE_CLASS[insight.severity]}`}>
            {t(`insight.severity.${insight.severity}`)}
          </span>
          <p className={`mt-xs text-body font-semibold ${dismissed ? "text-ink_body" : "text-ink_hero"}`}>{insight.title}</p>
          <p className={`mt-xs text-caption ${dismissed ? "text-ink_body/70" : "text-ink_hero/80"}`}>{body}</p>
        </div>
        <button
          type="button"
          onClick={dismissed ? onRestore : onDismiss}
          aria-label={dismissed ? t("insight.restore") : t("common.done")}
          className={`flex min-h-tap-min min-w-tap-min shrink-0 items-center justify-center rounded-full text-headline ${dismissed ? "text-ink_body" : "text-ink_hero"}`}
        >
          {dismissed ? "↺" : "×"}
        </button>
      </div>

      {evidenceEntries.length > 0 && (
        <div className="mt-sm">
          <button
            type="button"
            onClick={() => setShowWhy((v) => !v)}
            className={`min-h-tap-min text-caption underline ${dismissed ? "text-ink_body" : "text-ink_hero"}`}
          >
            {t("insight.show_why")}
          </button>
          {showWhy && (
            <dl className="mt-xs flex flex-col gap-xs text-caption">
              {evidenceEntries.map(([key, value]) => (
                <div key={key} className="flex justify-between gap-sm">
                  <dt className={dismissed ? "text-ink_body/70" : "text-ink_hero/80"}>{key.replace(/_/g, " ")}</dt>
                  <dd className={dismissed ? "text-ink_body" : "text-ink_hero"}>{String(value)}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      )}

      {!dismissed && insight.suggested_actions.length > 0 && (
        <div className="mt-sm flex flex-wrap gap-sm">
          {insight.suggested_actions.map((action) => (
            <SpiceChip key={action} label={action} tone="dark" onClick={onSuggestedAction} />
          ))}
        </div>
      )}
    </div>
  );
}

export function Insights() {
  const { t, i18n } = useTranslation();
  const userId = getCurrentUserId()!;
  const [insights, setInsights] = useState<Insight[]>([]);
  const [dismissed, setDismissed] = useState<string[]>(loadDismissed());
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    api.GET("/insights/{user_id}", { params: { path: { user_id: userId } } }).then(({ data }) => data && setInsights(data));
  }, [userId]);

  function dismiss(id: string) {
    const next = [...dismissed, id];
    setDismissed(next);
    saveDismissed(next);
  }

  function restore(id: string) {
    const next = dismissed.filter((d) => d !== id);
    setDismissed(next);
    saveDismissed(next);
  }

  const sorted = [...insights].sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity));
  const active = sorted.filter((i) => !dismissed.includes(i.insight_id));
  const dismissedToday = sorted.filter((i) => dismissed.includes(i.insight_id));
  const bodyField = (i18n.language in INSIGHT_BODY_FIELD ? i18n.language : "en") as keyof typeof INSIGHT_BODY_FIELD;

  return (
    <div className="flex flex-col gap-md p-md pb-32">
      <SignboardHeader title={t("nav.insights")} />

      {active.length === 0 && dismissedToday.length === 0 && (
        <p className="text-body text-ink_body/70">{t("insight.none")}</p>
      )}

      {active.map((insight) => (
        <InsightCard
          key={insight.insight_id}
          insight={insight}
          bodyField={bodyField}
          dismissed={false}
          onDismiss={() => dismiss(insight.insight_id)}
          onRestore={() => restore(insight.insight_id)}
          onSuggestedAction={() => setSheetOpen(true)}
        />
      ))}

      {dismissedToday.length > 0 && (
        <div className="mt-md">
          <h2 className="mb-sm text-headline font-display-latin text-ink_body">{t("insight.dismissed_today")}</h2>
          <div className="flex flex-col gap-sm">
            {dismissedToday.map((insight) => (
              <InsightCard
                key={insight.insight_id}
                insight={insight}
                bodyField={bodyField}
                dismissed={true}
                onDismiss={() => dismiss(insight.insight_id)}
                onRestore={() => restore(insight.insight_id)}
                onSuggestedAction={() => setSheetOpen(true)}
              />
            ))}
          </div>
        </div>
      )}

      <LogEntryFlow open={sheetOpen} userId={userId} onClose={() => setSheetOpen(false)} onLogged={() => setSheetOpen(false)} />
    </div>
  );
}
