// Yoruba is tonal: low (grave), mid (unmarked), high (acute). The seven
// vowels plus the syllabic nasals m/n carry tone; consonants do not.
// Values are ordered [low, mid, high]; mid is the bare base character.
// ẹ/ọ/m use combining marks (U+0300 / U+0301) since no precomposed glyph
// exists; n uses precomposed ǹ/ń, m uses precomposed ḿ.
export const TONES: Record<string, [string, string, string]> = {
  a: ["à", "a", "á"],
  e: ["è", "e", "é"],
  ẹ: ["ẹ̀", "ẹ", "ẹ́"],
  i: ["ì", "i", "í"],
  o: ["ò", "o", "ó"],
  ọ: ["ọ̀", "ọ", "ọ́"],
  u: ["ù", "u", "ú"],
  m: ["m̀", "m", "ḿ"],
  n: ["ǹ", "n", "ń"],
};

export function hasTones(base: string): boolean {
  return base in TONES;
}

export function toneVariants(base: string): [string, string, string] | null {
  return TONES[base] ?? null;
}
