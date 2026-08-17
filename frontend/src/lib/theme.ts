const STORAGE_KEY = "dalgains_dark_mode";

function apply(dark: boolean): void {
  document.documentElement.classList.toggle("dark", dark);
}

export function isDarkModeOn(): boolean {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored !== null) return stored === "true";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

export function setDarkMode(dark: boolean): void {
  localStorage.setItem(STORAGE_KEY, String(dark));
  apply(dark);
}

// Called once at app startup so the class is right before first paint,
// not just after a user visits Profile and toggles something.
export function initTheme(): void {
  apply(isDarkModeOn());
}
