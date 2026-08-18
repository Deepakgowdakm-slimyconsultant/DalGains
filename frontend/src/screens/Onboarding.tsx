import { useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { DhabaButton } from "../components/DhabaButton";
import { SpiceChip } from "../components/SpiceChip";
import { KatoriProgressRing } from "../components/KatoriProgressRing";
import { Footer } from "../components/Footer";
import { api } from "../api/client";
import { getCurrentUserId, setCurrentUserId } from "../lib/currentUser";
import type { components } from "../api/schema.gen";

type UserProfile = components["schemas"]["UserProfile"];
type PlanRecommendation = components["schemas"]["PlanRecommendation"];

type Draft = Partial<UserProfile>;

const SEX_OPTIONS: UserProfile["sex"][] = ["male", "female"];
const ACTIVITY_OPTIONS: UserProfile["activity_level"][] = [
  "sedentary",
  "light",
  "moderate",
  "active",
  "very_active",
];
const GOAL_OPTIONS: UserProfile["goal"][] = ["cut", "maintain", "lean_bulk", "recomp"];
const DIETARY_OPTIONS: UserProfile["dietary_pattern"][] = [
  "vegetarian",
  "vegan",
  "eggetarian",
  "non_vegetarian",
  "jain",
  "satvik",
  "custom",
];
const FASTING_OPTIONS: UserProfile["fasting_protocol"][] = [
  "none",
  "16_8",
  "18_6",
  "20_4",
  "omad",
  "5_2",
];

/** One question per screen (CLAUDE.md), wrapped in the same signboard
 * chrome every step. */
function Step({
  title,
  subtitle,
  children,
  onBack,
  onContinue,
  continueDisabled,
  continueLabel,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  onBack?: () => void;
  onContinue: () => void;
  continueDisabled?: boolean;
  continueLabel: string;
}) {
  return (
    <main className="flex min-h-dvh flex-col gap-lg p-md">
      <SignboardHeader title={title} subtitle={subtitle} />
      <div className="flex-1">{children}</div>
      <div className="flex gap-sm">
        {onBack && (
          <DhabaButton variant="secondary" onClick={onBack}>
            &larr;
          </DhabaButton>
        )}
        <div className="flex-1">
          <DhabaButton onClick={onContinue} disabled={continueDisabled} className="w-full">
            {continueLabel}
          </DhabaButton>
        </div>
      </div>
      <Footer />
    </main>
  );
}

const FASTING_LABELS: Record<string, string> = {
  none: "None",
  "16_8": "16:8",
  "18_6": "18:6",
  "20_4": "20:4",
  omad: "OMAD",
  "5_2": "5:2",
};

function ChipGrid<T extends string>({
  options,
  value,
  onChange,
  formatLabel = (opt) => opt.replace(/_/g, " "),
}: {
  options: readonly T[];
  value: T | undefined;
  onChange: (v: T) => void;
  formatLabel?: (opt: T) => string;
}) {
  return (
    <div className="flex flex-wrap gap-sm">
      {options.map((opt) => (
        <SpiceChip key={opt} label={formatLabel(opt)} selected={value === opt} onClick={() => onChange(opt)} />
      ))}
    </div>
  );
}

function NumberField({ value, onChange, placeholder }: { value: number | undefined; onChange: (v: number) => void; placeholder: string }) {
  return (
    <input
      type="number"
      inputMode="decimal"
      value={value ?? ""}
      placeholder={placeholder}
      onChange={(e) => onChange(Number(e.target.value))}
      className="min-h-tap-primary w-full rounded-md border-2 border-tamarind_brown/30 bg-surface_card px-md text-headline text-ink_body"
    />
  );
}

const STEPS = [
  "consent",
  "name",
  "age",
  "sex",
  "height",
  "weight",
  "activity",
  "goal",
  "dietary",
  "fasting",
  "plan_summary",
  "unit_calibration",
] as const;

export function Onboarding() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [stepIndex, setStepIndex] = useState(0);
  // The authenticated session's own id (App.tsx's AuthGate guarantees
  // this is populated before Onboarding renders) -- not a client-
  // generated crypto.randomUUID() like before Phase 5's auth. The
  // backend rejects a profile whose user_id doesn't match the session.
  const [draft, setDraft] = useState<Draft>({ user_id: getCurrentUserId()!, medical_flags: [] });
  const [plan, setPlan] = useState<PlanRecommendation | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [consented, setConsented] = useState(false);

  const step = STEPS[stepIndex];
  const goNext = () => setStepIndex((i) => Math.min(i + 1, STEPS.length - 1));
  const goBack = () => setStepIndex((i) => Math.max(i - 1, 0));

  async function submitProfile() {
    setSaving(true);
    setError(null);
    try {
      const body: UserProfile = {
        eating_phase: "maintenance",
        fasting_protocol: draft.fasting_protocol ?? "none",
        medical_flags: [],
        ...draft,
      } as UserProfile;
      const { data, error: apiError } = await api.POST("/profile", { body });
      if (apiError || !data) throw new Error("Could not save profile");
      setCurrentUserId(data.user_id);
      const planResp = await api.GET("/profile/{user_id}/plan", { params: { path: { user_id: data.user_id } } });
      if (planResp.error || !planResp.data) throw new Error("Could not generate plan");
      setPlan(planResp.data);
      goNext();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  switch (step) {
    case "consent":
      return (
        <Step
          title={t("onboarding.consent_title")}
          onContinue={goNext}
          continueLabel={t("common.confirm")}
          continueDisabled={!consented}
        >
          <label className="flex min-h-tap-primary items-start gap-sm rounded-md bg-surface_card p-md text-body text-ink_body">
            <input
              type="checkbox"
              checked={consented}
              onChange={(e) => setConsented(e.target.checked)}
              className="mt-1 h-6 w-6 shrink-0"
            />
            <span>
              {t("onboarding.consent_agree_prefix")}{" "}
              <Link to="/terms" target="_blank" className="underline">
                {t("onboarding.consent_terms_link")}
              </Link>{" "}
              {t("onboarding.consent_and")}{" "}
              <Link to="/privacy" target="_blank" className="underline">
                {t("onboarding.consent_privacy_link")}
              </Link>
              .
            </span>
          </label>
        </Step>
      );
    case "name":
      return (
        <Step title={t("onboarding.name_title")} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.name}>
          <input
            type="text"
            value={draft.name ?? ""}
            placeholder={t("onboarding.name_placeholder")}
            onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
            className="min-h-tap-primary w-full rounded-md border-2 border-tamarind_brown/30 bg-surface_card px-md text-headline text-ink_body"
          />
        </Step>
      );
    case "age":
      return (
        <Step title={t("onboarding.age_title")} onBack={goBack} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.age}>
          <NumberField value={draft.age} onChange={(v) => setDraft((d) => ({ ...d, age: v }))} placeholder={t("onboarding.age_placeholder")} />
        </Step>
      );
    case "sex":
      return (
        <Step title={t("onboarding.sex_title")} onBack={goBack} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.sex}>
          <ChipGrid options={SEX_OPTIONS} value={draft.sex} onChange={(v) => setDraft((d) => ({ ...d, sex: v }))} />
        </Step>
      );
    case "height":
      return (
        <Step title={t("onboarding.height_title")} onBack={goBack} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.height_cm}>
          <NumberField value={draft.height_cm} onChange={(v) => setDraft((d) => ({ ...d, height_cm: v }))} placeholder="cm" />
        </Step>
      );
    case "weight":
      return (
        <Step title={t("onboarding.weight_title")} onBack={goBack} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.weight_kg}>
          <NumberField value={draft.weight_kg} onChange={(v) => setDraft((d) => ({ ...d, weight_kg: v }))} placeholder="kg" />
        </Step>
      );
    case "activity":
      return (
        <Step title={t("onboarding.activity_title")} onBack={goBack} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.activity_level}>
          <ChipGrid options={ACTIVITY_OPTIONS} value={draft.activity_level} onChange={(v) => setDraft((d) => ({ ...d, activity_level: v, body_type: d.body_type ?? "mesomorph" }))} />
        </Step>
      );
    case "goal":
      return (
        <Step title={t("onboarding.goal_title")} onBack={goBack} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.goal}>
          <ChipGrid options={GOAL_OPTIONS} value={draft.goal} onChange={(v) => setDraft((d) => ({ ...d, goal: v }))} />
        </Step>
      );
    case "dietary":
      return (
        <Step title={t("onboarding.dietary_title")} onBack={goBack} onContinue={goNext} continueLabel={t("common.confirm")} continueDisabled={!draft.dietary_pattern}>
          <ChipGrid options={DIETARY_OPTIONS} value={draft.dietary_pattern} onChange={(v) => setDraft((d) => ({ ...d, dietary_pattern: v }))} />
        </Step>
      );
    case "fasting":
      return (
        <Step
          title={t("onboarding.fasting_title")}
          subtitle={t("onboarding.fasting_subtitle")}
          onBack={goBack}
          onContinue={submitProfile}
          continueLabel={saving ? "..." : t("common.confirm")}
          continueDisabled={saving}
        >
          <ChipGrid
            options={FASTING_OPTIONS}
            value={draft.fasting_protocol}
            onChange={(v) => setDraft((d) => ({ ...d, fasting_protocol: v }))}
            formatLabel={(opt) => FASTING_LABELS[opt as string] ?? (opt as string)}
          />
          {error && <p className="mt-md text-caption text-accent_warning_text">{error}</p>}
        </Step>
      );
    case "plan_summary":
      return (
        <Step title={t("onboarding.plan_title")} onContinue={goNext} continueLabel={t("common.confirm")}>
          {plan && (
            <div className="flex flex-col items-center gap-lg rounded-md bg-surface_signboard p-lg">
              <KatoriProgressRing label={t("plan.daily_calorie_target")} current={plan.daily_kcal} target={plan.daily_kcal} size="primary" colorToken="accent_celebration" />
              <div className="grid w-full grid-cols-3 gap-sm text-center">
                <div>
                  <p className="text-headline text-ink_hero">{Math.round(plan.protein_g)}g</p>
                  <p className="text-caption text-ink_hero/80">{t("plan.protein_target")}</p>
                </div>
                <div>
                  <p className="text-headline text-ink_hero">{Math.round(plan.fat_g)}g</p>
                  <p className="text-caption text-ink_hero/80">{t("plan.fat_target")}</p>
                </div>
                <div>
                  <p className="text-headline text-ink_hero">{Math.round(plan.carbs_g)}g</p>
                  <p className="text-caption text-ink_hero/80">{t("plan.carbs_target")}</p>
                </div>
              </div>
            </div>
          )}
        </Step>
      );
    case "unit_calibration":
      return (
        <Step title={t("onboarding.calibration_title")} subtitle={t("onboarding.calibration_subtitle")} onContinue={() => navigate("/")} continueLabel={t("onboarding.use_defaults")}>
          <DhabaButton variant="secondary" className="w-full" onClick={() => navigate("/profile")}>
            {t("onboarding.calibrate_now")}
          </DhabaButton>
        </Step>
      );
  }
}
