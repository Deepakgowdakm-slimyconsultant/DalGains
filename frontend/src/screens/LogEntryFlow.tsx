import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { FloatingLogSheet } from "../components/FloatingLogSheet";
import { ThaliCard } from "../components/ThaliCard";
import { SpiceChip } from "../components/SpiceChip";
import { DhabaButton } from "../components/DhabaButton";
import { api } from "../api/client";
import { useVoiceInput } from "../lib/useVoiceInput";
import type { components } from "../api/schema.gen";

type Recipe = components["schemas"]["Recipe"];
type Ingredient = components["schemas"]["Ingredient"];
type NutritionTotals = components["schemas"]["NutritionTotals"];

type SearchResult = { kind: "recipe"; item: Recipe } | { kind: "ingredient"; item: Ingredient };

const HOUSEHOLD_UNITS = ["katori", "small_katori", "glass", "tsp", "tbsp", "mutthi", "plate", "piece"] as const;

// Web Speech API locale tags, keyed by our i18n locale codes.
const VOICE_LOCALE: Record<string, string> = { en: "en-IN", hi: "hi-IN", kn: "kn-IN" };

const MEAL_SLOTS = [
  { key: "breakfast", hour: 8 },
  { key: "lunch", hour: 13 },
  { key: "snack", hour: 17 },
  { key: "dinner", hour: 20 },
] as const;

type FlowStep = "search" | "unit" | "when" | "confirm";

interface LogEntryFlowProps {
  open: boolean;
  userId: string;
  onClose: () => void;
  onLogged: () => void;
}

/** The 4-step log-entry flow living inside FloatingLogSheet: search ->
 * unit -> when -> confirm+preview. Every value here is editable right up
 * until the final POST -- nothing is silently accepted (CLAUDE.md). */
export function LogEntryFlow({ open, userId, onClose, onLogged }: LogEntryFlowProps) {
  const { t, i18n } = useTranslation();
  const [step, setStep] = useState<FlowStep>("search");
  const [query, setQuery] = useState("");
  const voice = useVoiceInput((transcript) => setQuery(transcript));
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [ingredientResults, setIngredientResults] = useState<Ingredient[]>([]);
  const [selected, setSelected] = useState<SearchResult | null>(null);
  const [qty, setQty] = useState(1);
  const [unit, setUnit] = useState<string>("katori");
  const [when, setWhen] = useState<{ mode: "now" | "slot"; slot?: string }>({ mode: "now" });
  const [preview, setPreview] = useState<NutritionTotals | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setStep("search");
    setQuery("");
    setSelected(null);
    setQty(1);
    setUnit("katori");
    setWhen({ mode: "now" });
    setPreview(null);
    setError(null);
  }

  useEffect(() => {
    if (!open) reset();
  }, [open]);

  useEffect(() => {
    if (step !== "search") return;
    api.GET("/recipes", { params: { query: {} } }).then(({ data }) => {
      if (data) {
        const q = query.trim().toLowerCase();
        setRecipes(q ? data.filter((r) => r.name.toLowerCase().includes(q) || r.aliases.some((a) => a.toLowerCase().includes(q))) : data);
      }
    });
  }, [step, query]);

  useEffect(() => {
    if (step !== "search" || query.trim().length < 2) {
      setIngredientResults([]);
      return;
    }
    const handle = setTimeout(() => {
      api.GET("/ingredients", { params: { query: { query } } }).then(({ data }) => {
        if (data) setIngredientResults(data.slice(0, 15));
      });
    }, 250);
    return () => clearTimeout(handle);
  }, [step, query]);

  function selectResult(result: SearchResult) {
    setSelected(result);
    setUnit(result.kind === "recipe" ? "serving" : "katori");
    setQty(1);
    setStep("unit");
  }

  async function fetchPreview() {
    if (!selected) return;
    setError(null);
    if (selected.kind === "recipe") {
      const { data, error: apiError } = await api.GET("/recipes/{recipe_id}/nutrition", {
        params: { path: { recipe_id: selected.item.recipe_id }, query: { servings: qty, user_id: userId } },
      });
      if (apiError || !data) {
        setError(t("logging.preview_failed"));
        return;
      }
      setPreview(data);
    } else {
      const { data, error: apiError } = await api.GET("/ingredients/{ingredient_id}/nutrition", {
        params: { path: { ingredient_id: selected.item.ingredient_id }, query: { qty, unit, user_id: userId } },
      });
      if (apiError || !data) {
        setError(t("logging.preview_failed"));
        return;
      }
      setPreview(data);
    }
  }

  function goToWhen() {
    setStep("when");
  }

  async function goToConfirm() {
    setStep("confirm");
    await fetchPreview();
  }

  function timestampFor(): string {
    const now = new Date();
    if (when.mode === "now") return now.toISOString();
    const slot = MEAL_SLOTS.find((s) => s.key === when.slot);
    const stamped = new Date(now);
    stamped.setHours(slot?.hour ?? now.getHours(), 0, 0, 0);
    return stamped.toISOString();
  }

  async function confirmLog() {
    if (!selected) return;
    setSaving(true);
    setError(null);
    // outside_eating_window is a required field on the wire, but the
    // server always recomputes and overwrites it against the user's
    // actual fasting window (src.logging.engine.log_entry) -- the value
    // sent here is never trusted.
    const body =
      selected.kind === "recipe"
        ? { recipe_id: selected.item.recipe_id, qty, unit: "serving", timestamp: timestampFor(), outside_eating_window: false }
        : { ingredient_id: selected.item.ingredient_id, qty, unit, timestamp: timestampFor(), outside_eating_window: false };
    const { error: apiError } = await api.POST("/logs/{user_id}/entries", {
      params: { path: { user_id: userId } },
      body,
    });
    setSaving(false);
    if (apiError) {
      setError(t("logging.save_failed"));
      return;
    }
    onLogged();
    onClose();
  }

  const title =
    step === "search"
      ? t("logging.search_title")
      : step === "unit"
        ? t("logging.how_much_roughly")
        : step === "when"
          ? t("logging.when_title")
          : t("logging.confirm_title");

  return (
    <FloatingLogSheet open={open} title={title} onClose={onClose}>
      {step === "search" && (
        <div className="flex flex-col gap-sm p-md">
          <div className="flex items-center gap-sm">
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("logging.search_placeholder")}
              className="min-h-tap-primary w-full flex-1 rounded-md border-2 border-tamarind_brown/30 bg-surface_card px-md text-body text-ink_body"
            />
            {voice.isSupported && (
              <button
                type="button"
                onClick={() => (voice.isListening ? voice.stop() : voice.start(VOICE_LOCALE[i18n.language] ?? "en-IN"))}
                aria-label={voice.isListening ? t("logging.voice_stop") : t("logging.voice_start")}
                aria-pressed={voice.isListening}
                className={`flex min-h-tap-primary min-w-tap-primary shrink-0 items-center justify-center rounded-full border-2 border-accent_action text-headline ${voice.isListening ? "bg-accent_action text-coal_black" : "text-accent_action_text"}`}
              >
                🎤
              </button>
            )}
          </div>
          <div className="flex flex-col gap-xs">
            {recipes.map((r) => (
              <ThaliCard key={r.recipe_id} title={r.name} subtitle={r.region_tag} icon={<span>🍽️</span>} onClick={() => selectResult({ kind: "recipe", item: r })} />
            ))}
            {ingredientResults.map((i) => (
              <ThaliCard
                key={i.ingredient_id}
                title={i.name}
                subtitle={`${Math.round(i.energy_kcal_per_100g)} kcal / 100g`}
                icon={<span>🥕</span>}
                onClick={() => selectResult({ kind: "ingredient", item: i })}
              />
            ))}
          </div>
        </div>
      )}

      {step === "unit" && selected && (
        <div className="flex flex-col gap-md p-md">
          <ThaliCard title={selected.item.name} icon={<span>{selected.kind === "recipe" ? "🍽️" : "🥕"}</span>} />
          {selected.kind === "ingredient" && (
            <div className="flex flex-wrap gap-sm">
              {HOUSEHOLD_UNITS.map((u) => (
                <SpiceChip key={u} label={t(`unit.${u}`)} selected={unit === u} onClick={() => setUnit(u)} />
              ))}
              <SpiceChip label={t("unit.g")} selected={unit === "g"} onClick={() => setUnit("g")} />
            </div>
          )}
          <div className="flex items-center gap-md">
            <button
              type="button"
              onClick={() => setQty((q) => Math.max(0.5, q - 0.5))}
              className="flex min-h-tap-min min-w-tap-min items-center justify-center rounded-full border-2 border-accent_action text-headline text-accent_action_text"
              aria-label={t("logging.decrease_qty")}
            >
              &minus;
            </button>
            <span className="min-w-16 text-center text-headline text-ink_body">
              {qty} {selected.kind === "recipe" ? t("logging.servings") : t(`unit.${unit}` as const)}
            </span>
            <button
              type="button"
              onClick={() => setQty((q) => q + 0.5)}
              className="flex min-h-tap-min min-w-tap-min items-center justify-center rounded-full border-2 border-accent_action text-headline text-accent_action_text"
              aria-label={t("logging.increase_qty")}
            >
              +
            </button>
          </div>
          <DhabaButton onClick={goToWhen} className="w-full">
            {t("common.confirm")}
          </DhabaButton>
        </div>
      )}

      {step === "when" && (
        <div className="flex flex-col gap-md p-md">
          <SpiceChip label={t("logging.now")} selected={when.mode === "now"} onClick={() => setWhen({ mode: "now" })} />
          <div className="flex flex-wrap gap-sm">
            {MEAL_SLOTS.map((slot) => (
              <SpiceChip
                key={slot.key}
                label={t(`logging.meal_slot.${slot.key}`)}
                selected={when.mode === "slot" && when.slot === slot.key}
                onClick={() => setWhen({ mode: "slot", slot: slot.key })}
              />
            ))}
          </div>
          <DhabaButton onClick={goToConfirm} className="w-full">
            {t("common.confirm")}
          </DhabaButton>
        </div>
      )}

      {step === "confirm" && selected && (
        <div className="flex flex-col gap-md p-md">
          <ThaliCard title={selected.item.name} subtitle={t("logging.preview_subtitle")} icon={<span>{selected.kind === "recipe" ? "🍽️" : "🥕"}</span>} />
          {preview ? (
            <div className="grid grid-cols-2 gap-sm rounded-md bg-surface_signboard p-md text-ink_hero">
              <p>{t("logging.preview_kcal")}: {Math.round(preview.energy_kcal)}</p>
              <p>{t("logging.preview_protein")}: {Math.round(preview.protein_g)}g</p>
              <p>{t("logging.preview_fat")}: {Math.round(preview.fat_g)}g</p>
              <p>{t("logging.preview_carbs")}: {Math.round(preview.carbs_g)}g</p>
            </div>
          ) : (
            <p className="text-body text-ink_body">{t("logging.loading_preview")}</p>
          )}
          {error && <p className="text-caption text-accent_warning_text">{error}</p>}
          <div className="flex gap-sm">
            <DhabaButton variant="secondary" onClick={() => setStep("unit")}>
              {t("common.edit")}
            </DhabaButton>
            <div className="flex-1">
              <DhabaButton onClick={confirmLog} disabled={saving || !preview} className="w-full">
                {saving ? "..." : t("logging.add_to_log")}
              </DhabaButton>
            </div>
          </div>
        </div>
      )}
    </FloatingLogSheet>
  );
}
