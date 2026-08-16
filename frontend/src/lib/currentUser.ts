const STORAGE_KEY = "dalgains_user_id";

// Single-household, no-auth app (CLAUDE.md) -- "the current user" is
// just whichever profile onboarding created, persisted locally.
export function getCurrentUserId(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}

export function setCurrentUserId(userId: string): void {
  localStorage.setItem(STORAGE_KEY, userId);
}

export function clearCurrentUserId(): void {
  localStorage.removeItem(STORAGE_KEY);
}
