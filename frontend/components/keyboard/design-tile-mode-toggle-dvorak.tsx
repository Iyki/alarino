import type { KeyboardLayoutSet, LayoutPair } from "./mobile-keyboard";

// Dvorak-style ordering: high-frequency vowels on the home row, the
// Yoruba specials placed where the layout has slack. Uniform key sizing
// + centered rows keep all three rows visually balanced.
const YO: LayoutPair = {
  default: [
    "p y f g r l ẹ ọ",
    "a o e u i d h t n s",
    "{shift} j k b m w ṣ gb {bksp}",
    "{num} {space} {enter}",
  ],
  shift: [
    "P Y F G R L Ẹ Ọ",
    "A O E U I D H T N S",
    "{shift} J K B M W Ṣ GB {bksp}",
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
