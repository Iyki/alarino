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

// Press-and-hold options for the desktop hardware keyboard. Holding a
// vowel offers every Yoruba form of it: bare, both tones, and (for e/o)
// the sub-dot vowel with its own tones. First entry is the plain base so
// the hold can resolve back to what was already typed.
export const VOWEL_ACCENTS: Record<string, string[]> = {
  a: ["a", "à", "á"],
  e: ["e", "è", "é", "ẹ", "ẹ̀", "ẹ́"],
  i: ["i", "ì", "í"],
  o: ["o", "ò", "ó", "ọ", "ọ̀", "ọ́"],
  u: ["u", "ù", "ú"],
};

export function vowelAccents(base: string): string[] | null {
  return VOWEL_ACCENTS[base] ?? null;
}

// Every tone form (precomposed à/á, combining ẹ̀/ọ̀/m̀, and the bare mid
// base itself) mapped back to its base, so a just-typed vowel can be
// re-toned in place regardless of which form is already there.
const FORM_TO_BASE: Record<string, string> = {};
for (const [base, forms] of Object.entries(TONES)) {
  for (const form of forms) FORM_TO_BASE[form] = base;
}

// The tone-bearing character ending `before` (the text up to the caret),
// if any. Combining forms (ẹ̀ = ẹ + U+0300) are two code units, so the
// 2-char suffix is tried before the 1-char one.
export function retoneSuffix(
  before: string,
): { base: string; len: number } | null {
  const two = before.slice(-2);
  if (two.length === 2 && two in FORM_TO_BASE) {
    return { base: FORM_TO_BASE[two], len: 2 };
  }
  const one = before.slice(-1);
  if (one && one in FORM_TO_BASE) {
    return { base: FORM_TO_BASE[one], len: 1 };
  }
  return null;
}

export function hasTones(base: string): boolean {
  return base in TONES;
}

export function toneVariants(base: string): [string, string, string] | null {
  return TONES[base] ?? null;
}
