export type PopoverAlign = "left" | "center" | "right";

// Tile/ribbon layouts are fixed grids, so a key's index reliably predicts
// whether its tone popover would clip the left/right edge of the
// overflow-hidden surface. Bias the two outermost keys on each side to
// anchor toward the nearest edge instead of centering.
export function pickAlign(index: number, total: number): PopoverAlign {
  const edgeBuffer = total >= 6 ? 2 : 1;
  if (index < edgeBuffer) return "left";
  if (index >= total - edgeBuffer) return "right";
  return "center";
}

export function popoverAlignClass(align: PopoverAlign): string {
  if (align === "left") return "left-0 translate-x-0";
  if (align === "right") return "right-0 left-auto translate-x-0";
  return "left-1/2 -translate-x-1/2";
}
