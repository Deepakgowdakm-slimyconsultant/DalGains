import { afterEach, describe, expect, it } from "vitest";
import { clearCurrentUserId, getCurrentUserId, setCurrentUserId } from "./currentUser";

describe("currentUser", () => {
  afterEach(() => localStorage.clear());

  it("returns null when no user has been set", () => {
    expect(getCurrentUserId()).toBeNull();
  });

  it("persists and returns the set user id", () => {
    setCurrentUserId("abc-123");
    expect(getCurrentUserId()).toBe("abc-123");
  });

  it("clears the persisted user id", () => {
    setCurrentUserId("abc-123");
    clearCurrentUserId();
    expect(getCurrentUserId()).toBeNull();
  });
});
