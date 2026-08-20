const STORAGE_KEY = "dalgains_user_id";

// A local cache of the server-verified user id (see src/lib/auth.ts and
// App.tsx's AuthGate, which populates this right after GET /auth/me
// succeeds) -- kept as a plain localStorage read/write, unchanged from
// before Phase 5's auth, so every screen that already calls
// getCurrentUserId() didn't need to change. The difference is *what*
// populates it: previously a client-generated crypto.randomUUID() from
// onboarding, now always the authenticated session's own id.
export function getCurrentUserId(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}

export function setCurrentUserId(userId: string): void {
  localStorage.setItem(STORAGE_KEY, userId);
}

export function clearCurrentUserId(): void {
  localStorage.removeItem(STORAGE_KEY);
}
