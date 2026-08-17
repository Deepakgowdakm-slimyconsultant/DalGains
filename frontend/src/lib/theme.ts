const DARK_KEY = "dalgains_dark_mode";
const BIG_TEXT_KEY = "dalgains_big_text";

function applyDark(dark: boolean): void {
  document.documentElement.classList.toggle("dark", dark);
}

function applyBigText(bigText: boolean): void {
  document.documentElement.classList.toggle("big-text", bigText);
}

export function isDarkModeOn(): boolean {
  const stored = localStorage.getItem(DARK_KEY);
  if (stored !== null) return stored === "true";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

export function setDarkMode(dark: boolean): void {
  localStorage.setItem(DARK_KEY, String(dark));
  applyDark(dark);
}

export function isBigTextOn(): boolean {
  return localStorage.getItem(BIG_TEXT_KEY) === "true";
}

export function setBigText(bigText: boolean): void {
  localStorage.setItem(BIG_TEXT_KEY, String(bigText));
  applyBigText(bigText);
}

// Called once at app startup so both classes are right before first
// paint, not just after a user visits Profile and toggles something.
export function initTheme(): void {
  applyDark(isDarkModeOn());
  applyBigText(isBigTextOn());
}
