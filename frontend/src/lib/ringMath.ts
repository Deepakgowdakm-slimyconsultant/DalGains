export interface RingGeometry {
  fraction: number;
  circumference: number;
  dashOffset: number;
  overTarget: boolean;
}

/** Pure display math behind KatoriProgressRing -- how full the ring draws
 * for a given current/target pair, independent of SVG rendering so it can
 * be property-tested directly. */
export function ringGeometry(current: number, target: number, radius: number): RingGeometry {
  const circumference = 2 * Math.PI * radius;
  const fraction = target > 0 ? Math.min(current / target, 1) : 0;
  const dashOffset = circumference * (1 - fraction);
  const overTarget = target > 0 && current > target;
  return { fraction, circumference, dashOffset, overTarget };
}
