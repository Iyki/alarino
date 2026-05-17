"use client";

import { ModeToggleKeyboard, type KeyRows } from "./tile-keyboard";

// Dvorak-style ordering: high-frequency vowels on the home row, special
// characters placed where the layout has natural slack so every row
// stays close to the same width without fixed-basis padding.
const YO_ROWS: KeyRows = [
  ["p", "y", "f", "g", "r", "l", "ẹ", "ọ"],
  ["a", "o", "e", "u", "i", "d", "h", "t", "n", "s"],
  ["j", "k", "b", "m", "w", "ṣ", "gb"],
];

const EN_ROWS: KeyRows = [
  ["p", "y", "f", "g", "c", "r", "l"],
  ["a", "o", "e", "u", "i", "d", "h", "t", "n", "s"],
  ["q", "j", "k", "x", "b", "m", "w", "v", "z"],
];

const LETTER_STYLE = { flex: "1 1 0", minWidth: 0 } as const;
const MOD_STYLE = { flex: "1.5 1.5 0", minWidth: 0 } as const;

export function DesignTileModeToggleDvorak() {
  return (
    <ModeToggleKeyboard
      yoRows={YO_ROWS}
      enRows={EN_ROWS}
      letterStyle={LETTER_STYLE}
      modStyle={MOD_STYLE}
    />
  );
}
