"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import { getCaretCoordinates } from "./caret-coordinates";
import { vowelAccents } from "./tones";

export interface AccentState {
  base: string;
  options: string[];
  left: number;
  top: number;
}

interface Pending {
  base: string; // lowercase vowel
  typed: string; // what a plain tap should insert (respects shift)
  anchor: number; // caret index where text is inserted
  timer: ReturnType<typeof setTimeout> | null;
  opened: boolean;
}

const HOLD_MS = 300;

// macOS-style press-and-hold for a hardware keyboard, WITHOUT the native
// accent menu. We preventDefault the vowel keydown — in Chromium that
// suppresses both the OS accent popup and the native character insertion
// — then drive the hold from our own timer and own all insertion. A
// quick tap inserts the plain vowel on keyup; a hold opens the Yoruba
// panel; any dismissal without a pick still inserts the plain vowel so a
// keystroke is never lost. (Safari can't be stopped from JS; it needs the
// system ApplePressAndHoldEnabled setting.)
export function useHoldAccents(
  textareaRef: RefObject<HTMLTextAreaElement | null>,
  value: string,
  setValue: (v: string) => void,
) {
  const [accent, setAccent] = useState<AccentState | null>(null);

  const valueRef = useRef(value);
  valueRef.current = value;
  const pending = useRef<Pending | null>(null);
  const accentRef = useRef<AccentState | null>(null);
  accentRef.current = accent;

  const reset = useCallback(() => {
    const p = pending.current;
    if (p?.timer) clearTimeout(p.timer);
    pending.current = null;
    setAccent(null);
  }, []);

  // Insert `text` at the stored caret, then drop the panel.
  const commit = useCallback(
    (text: string) => {
      const el = textareaRef.current;
      const p = pending.current;
      if (!el || !p) {
        reset();
        return;
      }
      const a = p.anchor;
      const v = valueRef.current;
      setValue(v.slice(0, a) + text + v.slice(a));
      const caret = a + text.length;
      requestAnimationFrame(() => {
        el.focus();
        el.setSelectionRange(caret, caret);
      });
      reset();
    },
    [reset, setValue, textareaRef],
  );

  const choose = useCallback((variant: string) => commit(variant), [commit]);
  // Dismiss without choosing → still emit the plain vowel.
  const close = useCallback(() => {
    const p = pending.current;
    if (p) commit(p.typed);
    else reset();
  }, [commit, reset]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    const openPanel = () => {
      const p = pending.current;
      if (!p) return;
      const c = getCaretCoordinates(el, p.anchor);
      const opts = vowelAccents(p.base) ?? [p.base];
      const upper = p.typed !== p.base;
      p.opened = true;
      setAccent({
        base: p.base,
        options: upper ? opts.map((o) => o.toUpperCase()) : opts,
        left: c.left - el.scrollLeft,
        top: c.top - el.scrollTop + c.height + 4,
      });
    };

    const onKeyDown = (e: KeyboardEvent) => {
      const p = pending.current;

      if (p?.opened) {
        if (e.key === "Escape") {
          e.preventDefault();
          commit(p.typed);
          return;
        }
        if (/^[1-9]$/.test(e.key)) {
          const idx = Number(e.key) - 1;
          const opt = accentRef.current?.options[idx];
          if (opt) {
            e.preventDefault();
            commit(opt);
          }
          return;
        }
        e.preventDefault(); // freeze typing while the panel is open
        return;
      }

      if (e.key.length !== 1 || e.ctrlKey || e.metaKey || e.altKey) return;
      const base = e.key.toLowerCase();
      if (!vowelAccents(base)) return;

      // Owning the vowel: this preventDefault is what removes the native
      // press-and-hold popup (Chromium) and stops the native character.
      e.preventDefault();
      if (p) return; // already holding this/another vowel

      const anchor = el.selectionStart ?? valueRef.current.length;
      const next: Pending = {
        base,
        typed: e.key,
        anchor,
        opened: false,
        timer: null,
      };
      next.timer = setTimeout(openPanel, HOLD_MS);
      pending.current = next;
    };

    const onKeyUp = () => {
      const p = pending.current;
      if (p && !p.opened) commit(p.typed); // quick tap → plain vowel
    };

    el.addEventListener("keydown", onKeyDown);
    el.addEventListener("keyup", onKeyUp);
    return () => {
      el.removeEventListener("keydown", onKeyDown);
      el.removeEventListener("keyup", onKeyUp);
    };
  }, [commit, textareaRef]);

  return { accent, choose, close };
}
