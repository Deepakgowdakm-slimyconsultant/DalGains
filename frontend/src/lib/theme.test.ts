import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { initTheme, isBigTextOn, isDarkModeOn, setBigText, setDarkMode } from "./theme";

function mockMatchMedia(matches: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  );
}

describe("theme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark", "big-text");
  });
  afterEach(() => vi.unstubAllGlobals());

  it("falls back to the system prefers-color-scheme when no choice is stored", () => {
    mockMatchMedia(true);
    expect(isDarkModeOn()).toBe(true);

    mockMatchMedia(false);
    expect(isDarkModeOn()).toBe(false);
  });

  it("an explicit stored choice overrides the system preference", () => {
    mockMatchMedia(true); // system says dark...
    setDarkMode(false); // ...but the user explicitly chose light
    expect(isDarkModeOn()).toBe(false);
  });

  it("setDarkMode toggles the 'dark' class on <html>", () => {
    setDarkMode(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    setDarkMode(false);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("big text mode defaults to off and persists independently of dark mode", () => {
    expect(isBigTextOn()).toBe(false);
    setBigText(true);
    expect(isBigTextOn()).toBe(true);
    expect(document.documentElement.classList.contains("big-text")).toBe(true);
  });

  it("initTheme applies both stored preferences before first paint", () => {
    setDarkMode(true);
    setBigText(true);
    document.documentElement.classList.remove("dark", "big-text");

    initTheme();

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.classList.contains("big-text")).toBe(true);
  });
});
