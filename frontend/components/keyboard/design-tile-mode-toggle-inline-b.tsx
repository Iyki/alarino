import type { KeyboardLayoutSet, LayoutPair } from "./mobile-keyboard";

// Yoruba uses no c/q/v/x/z. The row-3 slots z x c v are relabelled to
// the Yoruba specials ẹ ọ ṣ gb. Yoruba has no q either, but the q slot
// keeps a non-interactive {blank} placeholder so the top row stays the
// standard 10 wide: that preserves the native half-key offset of the
// 9-key home row beneath it, which is the spatial anchor QWERTY muscle
// memory depends on. Every letter sits exactly where a touch-typist
// expects. Long-press ẹ/ọ for their tone marks (see tones.ts).
const YO: LayoutPair = {
  default: [
    "{blank} w e r t y u i o p",
    "a s d f g h j k l",
    "{shift} ẹ ọ ṣ gb b n m {bksp}",
    "{num} {space} {enter}",
  ],
  shift: [
    "{blank} W E R T Y U I O P",
    "A S D F G H J K L",
    "{shift} Ẹ Ọ Ṣ GB B N M {bksp}",
    "{num} {space} {enter}",
  ],
};

const EN: LayoutPair = {
  default: [
    "q w e r t y u i o p",
    "a s d f g h j k l",
    "{shift} z x c v b n m {bksp}",
    "{num} {space} {enter}",
  ],
  shift: [
    "Q W E R T Y U I O P",
    "A S D F G H J K L",
    "{shift} Z X C V B N M {bksp}",
    "{num} {space} {enter}",
  ],
};

export const QWERTY_LAYOUT: KeyboardLayoutSet = { yo: YO, en: EN };
