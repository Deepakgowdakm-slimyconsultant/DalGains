// Shared fixture data for MSW-mocked component tests -- shapes matching
// the real backend schemas (src/core/schemas.py), not hand-waved stubs.
import type { components } from "../../api/schema.gen";

export const mockProfile: components["schemas"]["UserProfile"] = {
  user_id: "test-user",
  name: "Asha",
  age: 29,
  sex: "female",
  height_cm: 162,
  weight_kg: 58,
  body_type: "mesomorph",
  activity_level: "moderate",
  goal: "maintain",
  target_body_fat_pct: null,
  dietary_pattern: "vegetarian",
  eating_phase: "maintenance",
  fasting_protocol: "none",
  fasting_window: null,
  medical_flags: [],
};

export const mockPlan: components["schemas"]["PlanRecommendation"] = {
  daily_kcal: 1994,
  protein_g: 93,
  fat_g: 55,
  carbs_g: 281,
  fiber_g_min: 30,
  water_ml_min: 2400,
  eating_window: { start_hour: 0, end_hour: 24, note: null },
  warnings: [],
  guidance_notes: ["Eat protein with every meal.", "Aim for 7-9 hours of sleep.", "Stay hydrated throughout the day."],
};

export const mockMealLog: components["schemas"]["MealLog"] = {
  log_id: "2026-08-17",
  user_id: "test-user",
  timestamp: "2026-08-17T13:00:00Z",
  entries: [
    {
      recipe_id: "dal_tadka_north",
      ingredient_id: null,
      qty: 1,
      unit: "serving",
      timestamp: "2026-08-17T13:00:00Z",
      outside_eating_window: false,
    },
  ],
  computed_totals: { energy_kcal: 201, protein_g: 10, fat_g: 6, carbs_g: 26, fiber_g: 5 },
  notes: null,
  tags: [],
};

export const mockInsights: components["schemas"]["Insight"][] = [
  {
    insight_id: "protein_low_1",
    kind: "nudge",
    severity: "suggest",
    title: "Protein has been low for 3 days",
    body_en: "Your protein has been under 80% of your 93g target for 3 days running.",
    body_hi: "आपका प्रोटीन 3 दिनों से आपके 93g लक्ष्य के 80% से कम रहा है।",
    body_kn: "ನಿಮ್ಮ ಪ್ರೋಟೀನ್ 3 ದಿನಗಳಿಂದ ನಿಮ್ಮ 93g ಗುರಿಯ 80% ಕ್ಕಿಂತ ಕಡಿಮೆ ಇದೆ.",
    evidence: { days_running: 3, target_g: 93 },
    suggested_actions: ["Rajma Chawal adds about 15g protein per serving"],
  },
];

export const mockRecipes: components["schemas"]["Recipe"][] = [
  {
    recipe_id: "dal_tadka_north",
    name: "Dal Tadka",
    aliases: ["yellow dal"],
    ingredients: [{ ingredient_id: "B021", qty: 150, unit: "g" }],
    oil_ghee: { type: "ghee", qty_g: 10 },
    servings: 1,
    region_tag: "north",
    meal_type: "lunch",
    is_fasting_safe: false,
    tags: [],
    created_by: "seed",
    notes: null,
  },
];

export const mockIngredient: components["schemas"]["Ingredient"] = {
  ingredient_id: "B021",
  name: "Red gram, dal",
  aliases: ["toor dal", "arhar dal"],
  energy_kcal_per_100g: 330.8,
  protein_g_per_100g: 21.7,
  fat_g_per_100g: 1.5,
  carbs_g_per_100g: 57.6,
  fiber_g_per_100g: 15.0,
  source: "IFCT",
  category: "dal",
  per_piece_g: null,
};

export const mockUnits: Record<string, components["schemas"]["HouseholdUnit"]> = {};

export const mockCategoryBreakdown: components["schemas"]["CategoryBreakdown"] = {
  by_category: {
    dal: { energy_kcal: 496.2, protein_g: 32.55, fat_g: 2.25, carbs_g: 86.4, fiber_g: 0 },
  },
  beverage_kcal_by_date: { "2026-08-17": 0 },
  total_kcal_by_date: { "2026-08-17": 201 },
};

export const mockWeeklySummary: components["schemas"]["WeeklySummary"] = {
  user_id: "test-user",
  week_start_date: "2026-08-11",
  week_end_date: "2026-08-17",
  days: Array.from({ length: 7 }, (_, i) => ({
    date: `2026-08-${11 + i}`,
    totals: { energy_kcal: 201, protein_g: 10, fat_g: 6, carbs_g: 26, fiber_g: 5 },
    target_kcal: 1994,
    adherence_pct: 11,
    entry_count: 1,
  })),
  averages: { energy_kcal: 201, protein_g: 10, fat_g: 6, carbs_g: 26, fiber_g: 5 },
  target_adherence_pct: 0,
  streak_days: 7,
  notable_days: ["Highest kcal: 2026-08-11 (201 kcal)"],
  warnings: [],
};
