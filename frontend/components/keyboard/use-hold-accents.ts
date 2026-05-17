"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import { getCaretCoordinates } from "./caret-coordinates";
import { vowelAccents } from "./tones";

export interface AccentState {
  base: string;
  options: string[];
  left: number;
  top: number;
  anchor: number;
}

// macOS-style press-and-hold for a hardware keyboard: hold a vowel and a
// panel of its Yoruba forms appears at the caret. The OS key-repeat delay
// is the long-press timer — the first keydown types the bare letter, the
// first auto-repeat opens the panel and freezes further input until the
// user picks a number, clicks an option, or presses Escape.
export function useHoldAccents(
  textareaRef: RefObject<HTMLTextAreaElement | null>,
  value: string,
  setValue: (v: string) => void,
) {
  const [accent, setAccent] = useState<AccentState | null>(null);

  const valueRef = useRef(value);
  valueRef.current = value;
  const accentRef = useRef<AccentState | null>(null);
  accentRef.current = accent;

  const close = useCallback(() => setAccent(null), []);

  const choose = useCallback(
    (variant: string) => {
      const el = textareaRef.current;
      const st = accentRef.current;
      if (!el || !st) {
        setAccent(null);
        return;
      }
      const v = valueRef.current;
      const a = st.anchor;
      const next =
        a >= 1 ? v.slice(0, a - 1) + variant + v.slice(a) : variant + v.slice(a);
      setValue(next);
      const caret = (a >= 1 ? a - 1 : a) + variant.length;
      requestAnimationFrame(() => {
        el.focus();
        el.setSelectionRange(caret, caret);
      });
      setAccent(null);
    },
    [setValue, textareaRef],
  );

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    const onKeyDown = (e: KeyboardEvent) => {
      const st = accentRef.current;
      if (st) {
        if (e.key === "Escape") {
          e.preventDefault();
          setAccent(null);
          return;
        }
        if (/^[1-9]$/.test(e.key)) {
          const idx = Number(e.key) - 1;
          if (idx < st.options.length) {
            e.preventDefault();
            choose(st.options[idx]);
          }
          return;
        }
        // Freeze typing while the panel is open.
        e.preventDefault();
        return;
      }

      if (e.key.length !== 1 || e.ctrlKey || e.metaKey || e.altKey) return;
      const base = e.key.toLowerCase();
      const opts = vowelAccents(base);
      if (!opts) return;
      if (e.repeat) {
        e.preventDefault();
        const pos = el.selectionStart ?? valueRef.current.length;
        const c = getCaretCoordinates(el, pos);
        const upper = e.key !== base;
        setAccent({
          base,
          options: upper ? opts.map((o) => o.toUpperCase()) : opts,
          left: c.left - el.scrollLeft,
          top: c.top - el.scrollTop + c.height + 4,
          anchor: pos,
        });
      }
    };

    el.addEventListener("keydown", onKeyDown);
    return () => el.removeEventListener("keydown", onKeyDown);
  }, [choose, textareaRef]);

  return { accent, choose, close };
}
