"use client";

import { ModeToggleKeyboard, type KeyRows } from "./tile-keyboard";

// QWERTY-inspired ordering filtered to the Yoruba alphabet so muscle
// memory carries over. The digraph "gb" lives on Row 3 alongside the
// short b/n/m cluster, keeping Rows 1–2 evenly spaced.
const YO_ROWS: KeyRows = [
  ["w", "e", "ẹ", "r", "t", "y", "u", "i", "o", "ọ", "p"],
  ["a", "s", "ṣ", "d", "f", "g", "h", "j", "k", "l"],
  ["gb", "b", "n", "m"],
];

const EN_ROWS: KeyRows = [
  ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
  ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
  ["z", "x", "c", "v", "b", "n", "m"],
];

// 11 letter columns; the two mod keys are 1.5× a letter. 60px == the 10
// 6px row gaps on the widest row (11 cells), kept out of the basis math
// so the fixed-width letters never overflow the keyboard tray.
const LETTER_STYLE = { flex: "0 0 calc((100% - 60px) / 11)", minWidth: 0 } as const;
const MOD_STYLE = { flex: "0 0 calc(1.5 * (100% - 60px) / 11)", minWidth: 0 } as const;

export function DesignTileModeToggleInlineB() {
  return (
    <ModeToggleKeyboard
      yoRows={YO_ROWS}
      enRows={EN_ROWS}
      letterStyle={LETTER_STYLE}
      modStyle={MOD_STYLE}
    />
  );
}
