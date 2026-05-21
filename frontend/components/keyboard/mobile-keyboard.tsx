"use client";

import { type CSSProperties, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Keyboard from "react-simple-keyboard";

import "react-simple-keyboard/build/css/index.css";
import "./keyboard-theme.css";

import { CopyClearBar, type ToneIndex, useKeyboardText } from "./keyboard-chrome";
import { hasTones, toneVariants } from "./tones";
import { useDismissOnOutsidePointer, useEdgeClamp, useLongPress } from "./use-long-press";

export interface LayoutPair {
  default: string[];
  shift: string[];
}

export interface KeyboardLayoutSet {
  yo: LayoutPair;
  en: LayoutPair;
}

export type MobileKeyboardProps = KeyboardLayoutSet;

type Lang = "yo" | "en";
type Mode = "abc" | "num";

// Exported for layout tests. Row 3 deliberately has no {abc}: the only
// "letters" return key is on row 4, where it sits in every layout.
export const NUM_LAYOUT: string[] = [
  "1 2 3 4 5 6 7 8 9 0",
  "- / : ; ( ) ₦ & @ \"",
  ". , ? ! ' {bksp}",
  "{abc} {space} {enter}",
];

const TONE_BUTTONS = "a e ẹ i o ọ u m n A E Ẹ I O Ọ U M N";
const SPECIAL_BUTTONS = "ẹ ọ ṣ gb Ẹ Ọ Ṣ GB";

// Post-vowel tone entry: tap a vowel, then a tone. Yorùbá is ~50%
// vowels and tone is obligatory, so this keystroke-after-vowel model
// (no 400ms hold) is on the critical path for half of all typing. The
// glyphs are a dotted circle (U+25CC) carrying the combining mark so
// the diacritic shows in isolation. Long-press stays as a fallback.
// Only low and high are offered — mid is the unmarked default you get
// by simply typing the vowel, so a dedicated mid key has nothing to do.
const TONE_KEYS: { label: string; aria: string; index: ToneIndex }[] = [
  { label: "◌̀", aria: "Low tone (grave) on the last vowel", index: 0 },
  { label: "◌́", aria: "High tone (acute) on the last vowel", index: 2 },
];

interface TonePopover {
  base: string;
  left: number;
  top: number;
}

// A short tactile tick on each keystroke — the single biggest perceived
// improvement to on-screen typing feel. Silently absent where the
// Vibration API is unsupported (iOS Safari, desktop).
function tick() {
  if (typeof navigator !== "undefined" && "vibrate" in navigator) {
    navigator.vibrate(8);
  }
}

export function MobileKeyboard({ yo, en }: MobileKeyboardProps) {
  const { ref, value, setValue, insert, backspace, retoneLast } =
    useKeyboardText();
  const [lang, setLang] = useState<Lang>("yo");
  const [mode, setMode] = useState<Mode>("abc");
  const [shiftOn, setShiftOn] = useState(false);
  const [tone, setTone] = useState<TonePopover | null>(null);

  const wrapRef = useRef<HTMLDivElement | null>(null);
  const suppress = useRef<string | null>(null);
  const insertRef = useRef(insert);
  insertRef.current = insert;
  // The exact (case-correct) character the long-pressed key would type,
  // re-emitted if the gesture ends without picking a tone.
  const holdBase = useRef<string | null>(null);

  // Focus the field on mount so the caret is visible immediately and the
  // first key press lands at a real cursor position. inputMode="none"
  // means this does not raise the device keyboard.
  useEffect(() => {
    ref.current?.focus({ preventScroll: true });
  }, [ref]);

  const clamp = useEdgeClamp(tone !== null);
  useDismissOnOutsidePointer(tone !== null, () => setTone(null));

  // The tone menu is opened by a long-press whose pointer is still down.
  // Resolve the option under the pointer on release so the natural
  // press → slide → lift gesture works (a plain onClick can't, since the
  // pointer went down on the key, not the option). Capture-phase + the
  // hit-test also stops the release from tapping through to the key
  // beneath. Discrete taps land here too; onClick stays only for
  // keyboard activation (no pointer events).
  useEffect(() => {
    if (tone === null) return;
    const onUp = (e: PointerEvent) => {
      const hit = document.elementFromPoint(e.clientX, e.clientY);
      const item = hit?.closest<HTMLElement>("[data-tone-value]");
      if (item) {
        // Picked a tone (slide-release or discrete tap).
        e.preventDefault();
        e.stopPropagation();
        tick();
        insertRef.current(item.dataset.toneValue ?? "");
      } else if (
        holdBase.current &&
        hit &&
        wrapRef.current?.contains(hit)
      ) {
        // Released on the keyboard without choosing → emit the plain
        // letter (iOS behaviour) so the keystroke is not lost.
        insertRef.current(holdBase.current);
      }
      // Released off the keyboard entirely → cancel, insert nothing.
      holdBase.current = null;
      setTone(null);
    };
    window.addEventListener("pointerup", onUp, true);
    return () => window.removeEventListener("pointerup", onUp, true);
  }, [tone]);

  const layout = useMemo(
    () => ({
      "yo-default": yo.default,
      "yo-shift": yo.shift,
      "en-default": en.default,
      "en-shift": en.shift,
      num: NUM_LAYOUT,
    }),
    [yo, en],
  );

  const layoutName =
    mode === "num" ? "num" : `${lang}-${shiftOn ? "shift" : "default"}`;

  // Column width unit, sized so the active layout's widest row fills
  // edge-to-edge. A letter (and the {blank} placeholder) is 1 column;
  // shift/backspace/123/enter are 1.5 (native ratio); {space} grows and
  // contributes nothing. So a 10-slot top row sets a 10-column grid and
  // the 9-key home row beneath it gets the native half-key offset, while
  // every letter keeps a stable x across shift/layout states.
  const cols = useMemo(() => {
    const weight = (token: string) => {
      if (token === "{space}") return 0;
      if (["{shift}", "{bksp}", "{enter}", "{num}", "{abc}"].includes(token)) {
        return 1.5;
      }
      return 1;
    };
    const rows = layout[layoutName as keyof typeof layout] ?? [];
    const max = Math.max(
      1,
      ...rows.map((r) =>
        r
          .trim()
          .split(/\s+/)
          .filter(Boolean)
          .reduce((sum, t) => sum + weight(t), 0),
      ),
    );
    return Math.ceil(max);
  }, [layout, layoutName]);

  // The {blank} placeholder exists only to preserve the QWERTY top-row
  // offset; it must not be focusable or announced as an empty button.
  // react-simple-keyboard doesn't accept per-key a11y props, so we set
  // them on the rendered node after each layout change.
  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;
    const blank = wrap.querySelector<HTMLElement>(
      '.hg-button[data-skbtn="{blank}"]',
    );
    if (blank) {
      blank.setAttribute("tabindex", "-1");
      blank.setAttribute("aria-hidden", "true");
    }
  }, [layoutName]);

  const display = useMemo(
    () => ({
      "{shift}": "⇧",
      "{bksp}": "⌫",
      "{enter}": "↵",
      "{space}": lang === "yo" ? "àyè" : "space",
      "{num}": "123",
      "{abc}": "ABC",
      // Zero-width space, not "" — react-simple-keyboard treats an empty
      // display string as "no override" and would print "blank".
      "{blank}": "​",
    }),
    [lang],
  );

  const buttonTheme = useMemo(() => {
    const themes: { class: string; buttons: string }[] = [
      { class: "kbd-mod", buttons: "{shift} {bksp} {num} {abc}" },
      { class: "kbd-enter", buttons: "{enter}" },
      { class: "kbd-blank", buttons: "{blank}" },
    ];
    if (shiftOn) themes.push({ class: "kbd-shift-on", buttons: "{shift}" });
    if (lang === "yo" && mode === "abc") {
      themes.push({ class: "kbd-special", buttons: SPECIAL_BUTTONS });
      themes.push({ class: "kbd-tone", buttons: TONE_BUTTONS });
    }
    return themes;
  }, [lang, mode, shiftOn]);

  const onKeyReleased = useCallback(
    (button: string) => {
      tick();
      switch (button) {
        case "{shift}":
          setShiftOn((s) => !s);
          return;
        case "{bksp}":
          backspace();
          return;
        case "{enter}":
          insert("\n");
          return;
        case "{space}":
          insert(" ");
          return;
        case "{num}":
          setMode("num");
          return;
        case "{abc}":
          setMode("abc");
          return;
        case "{blank}":
          return;
        default:
          if (suppress.current === button) {
            suppress.current = null;
            return;
          }
          insert(button);
      }
    },
    [backspace, insert],
  );

  const pendingToken = useRef<string | null>(null);
  const pendingEl = useRef<HTMLElement | null>(null);

  // Long press on a tone-capable key opens an accent popover. We listen on
  // the wrapper (capture) so we see the press before the library, find the
  // key via react-simple-keyboard's data-skbtn attribute, and on the long
  // hold flag the key so its release tap is swallowed by onKeyReleased.
  const press = useLongPress(() => {
    const token = pendingToken.current;
    const el = pendingEl.current;
    const wrap = wrapRef.current;
    if (!token || !el || !wrap) return;
    const base = token.toLowerCase();
    if (!hasTones(base)) return;
    const k = el.getBoundingClientRect();
    const w = wrap.getBoundingClientRect();
    suppress.current = token;
    holdBase.current = token;
    // Default above the key; for the top row that would clip past the
    // overflow-hidden tray, so flip below it instead. Either way the
    // popover stays inside the (tall) keyboard tray and visible.
    const relTop = k.top - w.top;
    const above = relTop - 56;
    const below = relTop + k.height + 8;
    setTone({
      base,
      left: k.left - w.left + k.width / 2,
      top: above < 4 ? below : above,
    });
  });

  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;

    const down = (e: PointerEvent) => {
      const target = (e.target as Element | null)?.closest(".hg-button");
      const token = target?.getAttribute("data-skbtn") ?? null;
      if (!token || token.includes("{")) return;
      if (lang !== "yo" || mode !== "abc" || !hasTones(token.toLowerCase()))
        return;
      pendingToken.current = token;
      pendingEl.current = target as HTMLElement;
      press.start();
    };
    const up = () => press.cancel();

    wrap.addEventListener("pointerdown", down, true);
    window.addEventListener("pointerup", up);
    window.addEventListener("pointercancel", up);
    return () => {
      wrap.removeEventListener("pointerdown", down, true);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("pointercancel", up);
    };
  }, [lang, mode, press]);

  const switchLang = (target: Lang) => {
    setLang(target);
    setMode("abc");
    setTone(null);
  };

  const langPill = (target: Lang, label: string) => (
    <button
      type="button"
      onClick={() => switchLang(target)}
      aria-pressed={lang === target}
      aria-label={`${label} keyboard`}
      className={`rounded-full px-4 py-1 text-[13px] font-semibold transition ${
        lang === target
          ? "bg-brand-forest text-white shadow-card"
          : "border border-brand-brown/15 bg-white text-brand-brown/60"
      }`}
    >
      {label}
    </button>
  );

  const variants = tone ? toneVariants(tone.base) : null;

  return (
    <>
      <div className="mx-auto w-full max-w-[480px]">
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          rows={2}
          // inputMode="none" keeps the caret, focus and selection but
          // tells the browser not to raise the device's own keyboard —
          // this on-screen keyboard is the only input method. Initial
          // focus is handled by the effect below (which uses
          // preventScroll); we deliberately avoid the autoFocus
          // attribute since it doesn't accept that option and can scroll
          // the page on mount on some mobile browsers.
          inputMode="none"
          aria-label="Yoruba keyboard text input"
          placeholder={lang === "yo" ? "Bẹ̀rẹ̀ sí kọ…" : "Start typing…"}
          className="w-full resize-none rounded-xl border border-brand-brown/15 bg-white p-3 text-[15px] text-brand-ink caret-brand-forest outline-none placeholder:text-brand-brown/40 focus:border-brand-forest"
        />

        <div className="mt-3 flex justify-center gap-2">
          {langPill("yo", "Yorùbá")}
          {langPill("en", "English")}
        </div>

        <CopyClearBar value={value} onClear={() => setValue("")} />
      </div>

      {/* The keyboard is pinned to the bottom of the viewport while
          typing (sticky, not a fixed overlay), but it lives in the page
          flow so the site footer scrolls into view BELOW it at the end
          of the page instead of being covered. The leading spacer keeps
          its natural position past the fold so it stays pinned even when
          the page content above is short. */}
      <div aria-hidden className="min-h-[22vh]" />

      <div className="sticky bottom-0 z-30 mx-[calc(50%-50vw)] w-screen border-t border-brand-brown/10 bg-brand-beige/95 pb-[env(safe-area-inset-bottom)] shadow-[0_-4px_16px_rgba(26,18,7,0.06)] backdrop-blur-sm">
        {lang === "yo" && mode === "abc" ? (
          <div
            role="group"
            aria-label="Tone marks"
            className="mx-auto grid w-full max-w-[480px] grid-cols-2 gap-1.5 px-2 pt-2"
          >
            {TONE_KEYS.map((t) => (
              <button
                key={t.aria}
                type="button"
                aria-label={t.aria}
                // Prevent the tap (mouse OR touch) from stealing focus
                // from the textarea — onPointerDown covers touch, where
                // onMouseDown fires too late. Keeps the caret visible
                // and retoneLast's selectionStart read accurate.
                onPointerDown={(e) => e.preventDefault()}
                onClick={() => {
                  tick();
                  retoneLast(t.index);
                }}
                className="flex h-9 items-center justify-center rounded-lg border border-brand-brown/15 bg-white text-[19px] text-brand-ink transition active:scale-[0.97] active:bg-brand-gold-light"
              >
                {t.label}
              </button>
            ))}
          </div>
        ) : null}

        <div
          ref={wrapRef}
          data-clip
          onContextMenu={(e) => e.preventDefault()}
          style={{ "--kbd-cols": cols } as CSSProperties}
          className="relative mx-auto w-full max-w-[480px] touch-manipulation select-none overflow-hidden px-1.5 py-3"
        >
          <Keyboard
            theme="hg-theme-default alarino-kbd"
            layoutName={layoutName}
            layout={layout}
            display={display}
            buttonTheme={buttonTheme}
            onKeyReleased={onKeyReleased}
            disableButtonHold
            useButtonTag
            preventMouseDownDefault
          />

          {tone && variants ? (
            <div
              ref={clamp.ref}
              data-picker-root=""
              style={{
                left: tone.left,
                top: tone.top,
                transform: "translateX(-50%)",
                ...clamp.style,
              }}
              role="menu"
              aria-label="Tone options"
              className="absolute z-20 flex gap-1 whitespace-nowrap rounded-xl border border-brand-brown/15 bg-white px-1.5 py-1 shadow-card-hover"
            >
              {variants.map((v) => {
                const out = shiftOn ? v.toUpperCase() : v;
                return (
                  <button
                    key={v}
                    type="button"
                    role="menuitem"
                    aria-label={`Insert ${out}`}
                    data-tone-value={out}
                    onClick={() => {
                      tick();
                      insert(out);
                      setTone(null);
                    }}
                    className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-cream text-lg font-semibold text-brand-ink transition hover:bg-brand-forest hover:text-white"
                  >
                    {out}
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}
