import { http, HttpResponse } from "msw";
import {
  mockProfile,
  mockPlan,
  mockMealLog,
  mockInsights,
  mockRecipes,
  mockIngredient,
  mockUnits,
  mockCategoryBreakdown,
  mockWeeklySummary,
} from "./fixtures";

const BASE = "http://localhost:8000";

// One handler set standing in for the whole FastAPI backend --
// component tests exercise real request/response shapes (via MSW),
// never a hand-rolled fetch mock, so a schema drift between frontend
// and backend shows up as a broken test, not silently.
export const handlers = [
  http.get(`${BASE}/profile/:userId`, () => HttpResponse.json(mockProfile)),
  http.post(`${BASE}/profile`, async ({ request }) => HttpResponse.json(await request.json(), { status: 201 })),
  http.put(`${BASE}/profile/:userId`, async ({ request }) => HttpResponse.json(await request.json())),
  http.delete(`${BASE}/profile/:userId`, () => new HttpResponse(null, { status: 204 })),
  http.get(`${BASE}/profile/:userId/plan`, () => HttpResponse.json(mockPlan)),
  http.get(`${BASE}/profile/:userId/weight`, () => HttpResponse.json({})),
  http.post(`${BASE}/profile/:userId/weight`, async ({ request }) => HttpResponse.json(await request.json(), { status: 201 })),

  http.get(`${BASE}/logs/:userId/day/:date`, () => HttpResponse.json(mockMealLog)),
  http.post(`${BASE}/logs/:userId/entries`, () => HttpResponse.json(mockMealLog, { status: 201 })),
  http.get(`${BASE}/logs/:userId/dates`, () => HttpResponse.json([mockMealLog.log_id])),
  http.get(`${BASE}/logs/:userId/range/:start/:end`, () => HttpResponse.json([mockMealLog])),
  http.get(`${BASE}/logs/:userId/week/:weekEnding`, () => HttpResponse.json(mockWeeklySummary)),
  http.get(`${BASE}/logs/:userId/category_breakdown/:start/:end`, () => HttpResponse.json(mockCategoryBreakdown)),
  http.post(`${BASE}/logs/:userId/day/:date/tags`, () => HttpResponse.json(mockMealLog)),

  http.get(`${BASE}/insights/:userId`, () => HttpResponse.json(mockInsights)),

  http.get(`${BASE}/units/:userId`, () => HttpResponse.json(mockUnits)),
  http.post(`${BASE}/units/:userId`, async ({ request }) => {
    const body = (await request.json()) as { unit_name: string; volume_ml: number; method: string };
    return HttpResponse.json(
      { user_id: "test-user", unit_name: body.unit_name, volume_ml: body.volume_ml, calibrated_at: new Date().toISOString(), calibration_method: body.method },
      { status: 201 }
    );
  }),

  http.get(`${BASE}/recipes`, () => HttpResponse.json(mockRecipes)),
  http.get(`${BASE}/recipes/:recipeId`, () => HttpResponse.json(mockRecipes[0])),
  http.get(`${BASE}/recipes/:recipeId/nutrition`, () => HttpResponse.json(mockMealLog.computed_totals)),

  http.get(`${BASE}/ingredients`, ({ request }) => {
    const query = new URL(request.url).searchParams.get("query") ?? "";
    return HttpResponse.json(query.trim().length >= 2 ? [mockIngredient] : []);
  }),
  http.get(`${BASE}/ingredients/:ingredientId`, () => HttpResponse.json(mockIngredient)),
  http.get(`${BASE}/ingredients/:ingredientId/nutrition`, () => HttpResponse.json(mockMealLog.computed_totals)),
];
