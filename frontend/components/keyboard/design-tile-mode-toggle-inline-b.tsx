import type { KeyboardLayoutSet, LayoutPair } from "./mobile-keyboard";

// QWERTY-familiar order filtered to the Yoruba alphabet so muscle memory
// carries over. The gb digraph sits on Row 3 with the b/n/m cluster;
// uniform key sizing + centered rows keep the short row balanced.
const YO: LayoutPair = {
  default: [
    "w e ẹ r t y u i o ọ p",
    "a s ṣ d f g h j k l",
    "{shift} gb b n m {bksp}",
    "{num} {space} {enter}",
  ],
  shift: [
    "W E Ẹ R T Y U I O Ọ P",
    "A S Ṣ D F G H J K L",
    "{shift} GB B N M {bksp}",
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
