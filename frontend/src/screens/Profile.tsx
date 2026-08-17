import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { SignboardHeader } from "../components/SignboardHeader";
import { SpiceChip } from "../components/SpiceChip";
import { DhabaButton } from "../components/DhabaButton";
import { api } from "../api/client";
import { clearCurrentUserId, getCurrentUserId } from "../lib/currentUser";
import type { components } from "../api/schema.gen";
import type { Locale } from "../i18n";
import { SUPPORTED_LOCALES } from "../i18n";
import { isDarkModeOn, setDarkMode } from "../lib/theme";

type UserProfile = components["schemas"]["UserProfile"];
type HouseholdUnit = components["schemas"]["HouseholdUnit"];

const DEFAULT_UNIT_ML: Record<string, number> = {
  katori: 150,
  small_katori: 100,
  glass: 200,
  large_glass: 300,
  tsp: 5,
  tbsp: 15,
  plate: 400,
};

const LOCALE_LABELS: Record<Locale, string> = { en: "English", hi: "हिन्दी", kn: "ಕನ್ನಡ" };

function SectionHeading({ children }: { children: string }) {
  return <h2 className="mb-sm text-headline font-display-latin text-ink_body">{children}</h2>;
}

export function Profile() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const userId = getCurrentUserId()!;
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [units, setUnits] = useState<Record<string, HouseholdUnit>>({});
  const [calibratingUnit, setCalibratingUnit] = useState<string | null>(null);
  const [calibrationInput, setCalibrationInput] = useState("");
  const [darkMode, setDarkModeState] = useState(isDarkModeOn());
  const [confirmingReset, setConfirmingReset] = useState(false);
  const [savedMessage, setSavedMessage] = useState(false);

  useEffect(() => {
    api.GET("/profile/{user_id}", { params: { path: { user_id: userId } } }).then(({ data }) => data && setProfile(data));
    api.GET("/units/{user_id}", { params: { path: { user_id: userId } } }).then(({ data }) => data && setUnits(data));
  }, [userId]);

  async function saveProfile() {
    if (!profile) return;
    const { data } = await api.PUT("/profile/{user_id}", { params: { path: { user_id: userId } }, body: profile });
    if (data) {
      setProfile(data);
      setSavedMessage(true);
      setTimeout(() => setSavedMessage(false), 2000);
    }
  }

  async function saveCalibration(unitName: string) {
    const ml = Number(calibrationInput);
    if (!ml || ml <= 0) return;
    const { data } = await api.POST("/units/{user_id}", {
      params: { path: { user_id: userId } },
      body: { unit_name: unitName, volume_ml: ml, method: "measured" },
    });
    if (data) setUnits((u) => ({ ...u, [unitName]: data }));
    setCalibratingUnit(null);
    setCalibrationInput("");
  }

  function switchLanguage(locale: Locale) {
    i18n.changeLanguage(locale);
  }

  function toggleDarkMode() {
    const next = !darkMode;
    setDarkModeState(next);
    setDarkMode(next);
  }

  function exportData() {
    const payload = { profile, exported_at: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dalgains-export-${userId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function resetData() {
    await api.DELETE("/profile/{user_id}", { params: { path: { user_id: userId } } });
    clearCurrentUserId();
    localStorage.removeItem("dalgains_dismissed_insights");
    navigate("/onboarding");
  }

  if (!profile) {
    return <div className="p-md text-body text-ink_body">{t("weekly.loading")}</div>;
  }

  return (
    <div className="flex flex-col gap-lg p-md pb-32">
      <SignboardHeader title={t("nav.profile")} />

      <section>
        <SectionHeading>{t("profile.your_details")}</SectionHeading>
        <div className="flex flex-col gap-sm rounded-md bg-surface_primary p-md">
          <label className="flex flex-col gap-xs text-caption text-ink_body/70">
            {t("onboarding.name_title")}
            <input
              type="text"
              value={profile.name}
              onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              className="min-h-tap-min rounded-md border-2 border-tamarind_brown/30 bg-signboard_white px-sm text-body text-ink_body"
            />
          </label>
          <label className="flex flex-col gap-xs text-caption text-ink_body/70">
            {t("onboarding.weight_title")}
            <input
              type="number"
              value={profile.weight_kg}
              onChange={(e) => setProfile({ ...profile, weight_kg: Number(e.target.value) })}
              className="min-h-tap-min rounded-md border-2 border-tamarind_brown/30 bg-signboard_white px-sm text-body text-ink_body"
            />
          </label>
          <DhabaButton onClick={saveProfile}>{savedMessage ? t("common.done") : t("common.save")}</DhabaButton>
        </div>
      </section>

      <section>
        <SectionHeading>{t("profile.calibration")}</SectionHeading>
        <div className="flex flex-col gap-xs rounded-md bg-surface_primary p-md">
          {Object.keys(DEFAULT_UNIT_ML).map((unitName) => {
            const calibrated = units[unitName];
            return (
              <div key={unitName} className="flex items-center justify-between gap-sm">
                <span className="text-body text-ink_body">{t(`unit.${unitName}`)}</span>
                {calibratingUnit === unitName ? (
                  <div className="flex items-center gap-xs">
                    <input
                      type="number"
                      autoFocus
                      value={calibrationInput}
                      onChange={(e) => setCalibrationInput(e.target.value)}
                      placeholder="ml"
                      className="min-h-tap-min w-20 rounded-md border-2 border-tamarind_brown/30 bg-signboard_white px-sm text-body text-ink_body"
                    />
                    <DhabaButton onClick={() => saveCalibration(unitName)}>{t("common.save")}</DhabaButton>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setCalibratingUnit(unitName);
                      setCalibrationInput(String(calibrated?.volume_ml ?? DEFAULT_UNIT_ML[unitName]));
                    }}
                    className="min-h-tap-min text-caption text-accent_action underline"
                  >
                    {calibrated ? `${calibrated.volume_ml}ml` : `${DEFAULT_UNIT_ML[unitName]}ml (${t("profile.default_label")})`}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <SectionHeading>{t("language.toggle")}</SectionHeading>
        <div className="flex gap-sm">
          {SUPPORTED_LOCALES.map((locale) => (
            <SpiceChip key={locale} label={LOCALE_LABELS[locale]} selected={i18n.language === locale} onClick={() => switchLanguage(locale)} />
          ))}
        </div>
      </section>

      <section className="flex items-center justify-between rounded-md bg-surface_primary p-md">
        <span className="text-body text-ink_body">{t("profile.dark_mode")}</span>
        <button
          type="button"
          role="switch"
          aria-checked={darkMode}
          onClick={toggleDarkMode}
          className={`flex min-h-tap-min w-16 items-center rounded-full p-1 transition-colors ${darkMode ? "bg-accent_action justify-end" : "bg-tamarind_brown/30 justify-start"}`}
        >
          <span className="h-6 w-6 rounded-full bg-signboard_white" />
        </button>
      </section>

      <section>
        <SectionHeading>{t("profile.data")}</SectionHeading>
        <div className="flex flex-col gap-sm">
          <DhabaButton variant="secondary" onClick={exportData} className="w-full">
            {t("profile.export_data")}
          </DhabaButton>
          {!confirmingReset ? (
            <DhabaButton variant="danger" onClick={() => setConfirmingReset(true)} className="w-full">
              {t("profile.reset_data")}
            </DhabaButton>
          ) : (
            <div className="flex flex-col gap-sm rounded-md bg-surface_signboard p-md">
              <p className="text-body text-ink_hero">{t("profile.reset_confirm")}</p>
              <div className="flex gap-sm">
                <DhabaButton variant="secondary" onClick={() => setConfirmingReset(false)} className="flex-1">
                  {t("common.cancel")}
                </DhabaButton>
                <DhabaButton variant="danger" onClick={resetData} className="flex-1">
                  {t("profile.reset_confirm_button")}
                </DhabaButton>
              </div>
            </div>
          )}
        </div>
      </section>

      <section>
        <SectionHeading>{t("profile.about")}</SectionHeading>
        <div className="rounded-md bg-surface_primary p-md text-caption text-ink_body/80">
          <p>{t("profile.license_notice")}</p>
          <p className="mt-sm font-semibold">{t("profile.medical_disclaimer")}</p>
        </div>
      </section>
    </div>
  );
}
