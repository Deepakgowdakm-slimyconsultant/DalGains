import { api } from "../api/client";
import type { components } from "../api/schema.gen";

export type CurrentUser = components["schemas"]["User"];

/** GET /auth/me -- null if not logged in (401), never throws for that
 * case since "not logged in" is an expected, common state, not an
 * error condition callers need to catch. */
export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  const { data, response } = await api.GET("/auth/me");
  if (response.status === 401) return null;
  return data ?? null;
}

export async function requestMagicLink(email: string): Promise<void> {
  // openapi-fetch never throws on a non-2xx response -- it resolves
  // {data, error} either way, so a caller wanting try/catch semantics
  // (Login.tsx's error message) has to check `response.ok` itself.
  const { response } = await api.POST("/auth/request-link", { body: { email } });
  if (!response.ok) throw new Error(`request-link failed: ${response.status}`);
}

export async function logout(): Promise<void> {
  await api.POST("/auth/logout");
}
