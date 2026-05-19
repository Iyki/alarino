import type { KeyboardLayoutSet, LayoutPair } from "./mobile-keyboard";

// Standard Dvorak with the slots Yoruba never uses repurposed for its
// specials: row 1's ' , . and c become ẹ ọ ṣ gb, so every Yoruba letter
// (p y f g r l, the full a-o-e-u-i-d-h-t-n-s home row, j k b m w) keeps
// its exact Dvorak position and a Dvorak typist's muscle memory carries
// over. Long-press ẹ/ọ for their tone marks (see tones.ts).
const YO: LayoutPair = {
  default: [
    "ẹ ọ ṣ p y f g gb r l",
    "a o e u i d h t n s",
    "{shift} j k b m w {bksp}",
    "{num} {space} {enter}",
  ],
  shift: [
    "Ẹ Ọ Ṣ P Y F G GB R L",
    "A O E U I D H T N S",
    "{shift} J K B M W {bksp}",
    "{num} {space} {enter}",
  ],
};

const EN: LayoutPair = {
  default: [
    "p y f g c r l",
    "a o e u i d h t n s",
    "{shift} q j k x b m w v z {bksp}",
    "{num} {space} {enter}",
  ],
  shift: [
    "P Y F G C R L",
    "A O E U I D H T N S",
    "{shift} Q J K X B M W V Z {bksp}",
    "{num} {space} {enter}",
  ],
};

export const DVORAK_LAYOUT: KeyboardLayoutSet = { yo: YO, en: EN };
