import { describe, expect, it } from "vitest";
import fc from "fast-check";
import { ringGeometry } from "./ringMath";

const nonNegative = fc.float({ min: 0, max: Math.fround(100000), noNaN: true });
const positiveRadius = fc.float({ min: Math.fround(0.01), max: Math.fround(1000), noNaN: true });

describe("ringGeometry", () => {
  it("fraction is always within [0, 1] for any current/target/radius", () => {
    fc.assert(
      fc.property(nonNegative, nonNegative, positiveRadius, (current, target, radius) => {
        const { fraction } = ringGeometry(current, target, radius);
        expect(fraction).toBeGreaterThanOrEqual(0);
        expect(fraction).toBeLessThanOrEqual(1);
      })
    );
  });

  it("dashOffset always falls within [0, circumference]", () => {
    fc.assert(
      fc.property(nonNegative, nonNegative, positiveRadius, (current, target, radius) => {
        const { dashOffset, circumference } = ringGeometry(current, target, radius);
        expect(dashOffset).toBeGreaterThanOrEqual(-1e-9);
        expect(dashOffset).toBeLessThanOrEqual(circumference + 1e-9);
      })
    );
  });

  it("a zero or negative target always yields an empty ring, never overTarget", () => {
    fc.assert(
      fc.property(nonNegative, fc.float({ min: -1000, max: 0, noNaN: true }), positiveRadius, (current, target, radius) => {
        const { fraction, overTarget, dashOffset, circumference } = ringGeometry(current, target, radius);
        expect(fraction).toBe(0);
        expect(overTarget).toBe(false);
        expect(dashOffset).toBeCloseTo(circumference, 6);
      })
    );
  });

  it("overTarget is exactly current > target when target is positive", () => {
    fc.assert(
      fc.property(nonNegative, fc.float({ min: Math.fround(0.01), max: Math.fround(100000), noNaN: true }), positiveRadius, (current, target, radius) => {
        const { overTarget } = ringGeometry(current, target, radius);
        expect(overTarget).toBe(current > target);
      })
    );
  });

  it("reaching exactly the target always fully fills the ring (dashOffset ~0)", () => {
    fc.assert(
      fc.property(fc.float({ min: Math.fround(0.01), max: Math.fround(100000), noNaN: true }), positiveRadius, (target, radius) => {
        const { fraction, dashOffset } = ringGeometry(target, target, radius);
        expect(fraction).toBeCloseTo(1, 6);
        expect(dashOffset).toBeCloseTo(0, 3);
      })
    );
  });
});
