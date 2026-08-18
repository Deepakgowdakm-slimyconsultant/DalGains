import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { components } from "../../api/schema.gen";

type UserProfile = components["schemas"]["UserProfile"];
type PlanRecommendation = components["schemas"]["PlanRecommendation"];
type MealLog = components["schemas"]["MealLog"];
type Recipe = components["schemas"]["Recipe"];

export interface RecipeInfo {
  name: string;
  meal_type: Recipe["meal_type"];
}

/** Shared data loading for every History tab (Timeline/Trends/Patterns):
 * profile, plan, and every real MealLog the user has, fetched once via
 * GET /logs/{user_id}/dates + a single GET .../range call rather than
 * one request per day. Also resolves recipe/ingredient display names,
 * since MealLog entries only carry ids.
 */
export function useHistoryData(userId: string) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [plan, setPlan] = useState<PlanRecommendation | null>(null);
  const [logs, setLogs] = useState<MealLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [recipes, setRecipes] = useState<Record<string, RecipeInfo>>({});
  const [ingredientNames, setIngredientNames] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      const [profileRes, planRes, datesRes, recipesRes] = await Promise.all([
        api.GET("/profile/{user_id}", { params: { path: { user_id: userId } } }),
        api.GET("/profile/{user_id}/plan", { params: { path: { user_id: userId } } }),
        api.GET("/logs/{user_id}/dates", { params: { path: { user_id: userId } } }),
        api.GET("/recipes", { params: { query: {} } }),
      ]);
      if (cancelled) return;

      setProfile(profileRes.data ?? null);
      setPlan(planRes.data ?? null);
      setRecipes(
        Object.fromEntries((recipesRes.data ?? []).map((r: Recipe) => [r.recipe_id, { name: r.name, meal_type: r.meal_type }]))
      );

      const dates = datesRes.data ?? [];
      if (dates.length === 0) {
        setLogs([]);
        setLoading(false);
        return;
      }

      const newest = dates[0];
      const oldest = dates[dates.length - 1];
      const rangeRes = await api.GET("/logs/{user_id}/range/{start}/{end}", {
        params: { path: { user_id: userId, start: oldest, end: newest } },
      });
      if (cancelled) return;

      const mealLogs = (rangeRes.data ?? []).filter((l): l is MealLog => "entries" in l);
      mealLogs.sort((a, b) => b.log_id.localeCompare(a.log_id));
      setLogs(mealLogs);
      setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  // Ingredient names aren't in the recipes fetch -- resolve lazily,
  // once per unique id, and cache.
  useEffect(() => {
    const missing = new Set<string>();
    for (const log of logs) {
      for (const entry of log.entries) {
        if (entry.ingredient_id && !ingredientNames[entry.ingredient_id]) missing.add(entry.ingredient_id);
      }
    }
    for (const id of missing) {
      api.GET("/ingredients/{ingredient_id}", { params: { path: { ingredient_id: id } } }).then(({ data }) => {
        if (data) setIngredientNames((names) => ({ ...names, [id]: data.name }));
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [logs]);

  function entryLabel(entry: MealLog["entries"][number]): string {
    if (entry.recipe_id) return recipes[entry.recipe_id]?.name ?? entry.recipe_id;
    return ingredientNames[entry.ingredient_id ?? ""] ?? entry.ingredient_id ?? "";
  }

  function dayIsBeveragesOnly(log: MealLog): boolean {
    return log.entries.length > 0 && log.entries.every((e) => e.recipe_id && recipes[e.recipe_id]?.meal_type === "beverage");
  }

  return { profile, plan, logs, loading, recipes, entryLabel, dayIsBeveragesOnly };
}
