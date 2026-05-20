"use client";

import { useCallback, useRef, useState } from "react";

import { retoneSuffix, TONES } from "./tones";

// Low / mid / high — indices into a TONES entry.
export type ToneIndex = 0 | 1 | 2;

// Canonical Unicode form. Yorùbá text mixes precomposed (á, é) and
// combining (ẹ̀ = ẹ + U+0300, which has no precomposed glyph) forms;
// normalising to NFC everywhere keeps stored, copied and counted text
// consistent.
export const toNFC = (s: string) => s.normalize("NFC");

// User-perceived character count: a tone-marked vowel is ONE character,
// even ẹ̀/ọ̀ which are two code units (base + combining mark). A tone
// mark is not a separate character. Intl.Segmenter is the correct
// grapheme splitter; fall back to stripping combining marks where it is
// unavailable.
type Segmenter = {
  segment(input: string): Iterable<{ segment: string }>;
};
const SegmenterCtor = (
  Intl as { Segmenter?: new (l?: unknown, o?: unknown) => Segmenter }
).Segmenter;

function graphemes(text: string): string[] {
  if (SegmenterCtor) {
    const seg = new SegmenterCtor(undefined, { granularity: "grapheme" });
    return Array.from(seg.segment(text), (s) => s.segment);
  }
  // Fallback: a base (or standalone) char plus any trailing combining marks.
  return text.match(/\P{M}\p{M}*|\p{M}+/gu) ?? [];
}

export function countCharacters(s: string): number {
  return graphemes(toNFC(s)).length;
}

// Code-unit length of the last user-perceived character, so backspace
// deletes a whole grapheme (e.g. ẹ̀ = ẹ + U+0300) rather than peeling
// off just the combining mark — keeping delete consistent with the
// character count and native keyboards.
export function lastGraphemeLength(s: string): number {
  if (!s) return 0;
  const g = graphemes(s);
  return g.length ? g[g.length - 1].length : 1;
}

// Shared textarea state + insert-at-cursor. Keeps the caret stable so
// successive key/tone presses build a continuous string.
export function useKeyboardText() {
  const ref = useRef<HTMLTextAreaElement | null>(null);
  const [value, setValueRaw] = useState("");

  // The single place the NFC invariant is enforced: every entry path
  // (both textareas' onChange, on-screen keys, hold-accents, tone strip,
  // clear) goes through this, so the buffer is never a mix of composed
  // and decomposed forms regardless of where text came from. Caveat:
  // pasting raw decomposed text shortens the controlled value by the
  // composition delta, so the browser caret can land off by that many
  // code units — rare in practice (our keys and copy emit NFC already)
  // and acceptable in exchange for the guarantee.
  const setValue = useCallback(
    (next: string | ((prev: string) => string)) =>
      setValueRaw((prev) =>
        toNFC(typeof next === "function" ? next(prev) : next),
      ),
    [],
  );

  const insert = useCallback((text: string) => {
    const el = ref.current;
    if (!el) {
      setValue((prev) => prev + text);
      return;
    }
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    const next = value.slice(0, start) + text + value.slice(end);
    setValue(next);
    requestAnimationFrame(() => {
      el.focus();
      const caret = start + text.length;
      el.setSelectionRange(caret, caret);
    });
  }, [value, setValue]);

  const backspace = useCallback(() => {
    const el = ref.current;
    if (!el) {
      setValue((prev) => prev.slice(0, prev.length - lastGraphemeLength(prev)));
      return;
    }
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    if (start === end && start === 0) return;
    // Delete a whole grapheme at the caret, not one UTF-16 unit, so
    // ẹ̀/ọ̀/m̀ vanish in one press instead of leaving the base behind.
    const from =
      start === end
        ? start - lastGraphemeLength(value.slice(0, start))
        : start;
    const next = value.slice(0, from) + value.slice(end);
    setValue(next);
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(from, from);
    });
  }, [value, setValue]);

  // Re-tone the vowel/syllabic-nasal immediately before the caret —
  // the "type the vowel, then pick its tone" model. No-op if the
  // preceding character can't carry tone.
  const retoneLast = useCallback(
    (toneIndex: ToneIndex) => {
      const el = ref.current;
      const start = el ? el.selectionStart ?? value.length : value.length;
      const match = retoneSuffix(value.slice(0, start));
      if (!match) return;
      const from = start - match.len;
      const replacement = TONES[match.base][toneIndex];
      const next = value.slice(0, from) + replacement + value.slice(start);
      setValue(next);
      if (el) {
        const caret = from + replacement.length;
        requestAnimationFrame(() => {
          el.focus();
          el.setSelectionRange(caret, caret);
        });
      }
    },
    [value, setValue],
  );

  return { ref, value, setValue, insert, backspace, retoneLast };
}

interface CopyClearBarProps {
  value: string;
  onClear: () => void;
}

export function CopyClearBar({ value, onClear }: CopyClearBarProps) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    const text = toNFC(value);
    try {
      // navigator.clipboard only exists in a secure context (https or
      // localhost). Over plain http — e.g. testing on a phone via the
      // LAN IP — it's undefined, so fall back to a hidden-textarea
      // execCommand("copy"), which works from this click gesture.
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const scratch = document.createElement("textarea");
        scratch.value = text;
        scratch.setAttribute("readonly", "");
        scratch.style.position = "fixed";
        scratch.style.top = "-9999px";
        document.body.appendChild(scratch);
        scratch.select();
        scratch.setSelectionRange(0, text.length);
        const ok = document.execCommand("copy");
        document.body.removeChild(scratch);
        if (!ok) throw new Error("execCommand copy rejected");
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }, [value]);

  return (
    <div className="mt-3 flex items-center justify-between text-xs text-brand-brown/70">
      <span>
        {(() => {
          const n = countCharacters(value);
          return `${n} character${n === 1 ? "" : "s"}`;
        })()}
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={copy}
          disabled={value.length === 0}
          className="rounded-lg border border-brand-brown/20 px-3 py-1.5 font-semibold text-brand-ink transition hover:border-brand-forest hover:text-brand-forest disabled:opacity-40"
        >
          {copied ? "Copied" : "Copy"}
        </button>
        <button
          type="button"
          onClick={onClear}
          disabled={value.length === 0}
          className="rounded-lg border border-brand-brown/20 px-3 py-1.5 font-semibold text-brand-ink transition hover:border-brand-terracotta hover:text-brand-terracotta disabled:opacity-40"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
