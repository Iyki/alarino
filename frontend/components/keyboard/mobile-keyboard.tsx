"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Keyboard from "react-simple-keyboard";

import "react-simple-keyboard/build/css/index.css";
import "./keyboard-theme.css";

import { CopyClearBar, useKeyboardText } from "./keyboard-chrome";
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

const NUM_LAYOUT: string[] = [
  "1 2 3 4 5 6 7 8 9 0",
  "- / : ; ( ) ₦ & @ \"",
  "{abc} . , ? ! ' {bksp}",
  "{abc} {space} {enter}",
];

const TONE_BUTTONS = "a e ẹ i o ọ u m n A E Ẹ I O Ọ U M N";
const SPECIAL_BUTTONS = "ẹ ọ ṣ gb Ẹ Ọ Ṣ GB";

interface TonePopover {
  base: string;
  left: number;
  top: number;
}

export function MobileKeyboard({ yo, en }: MobileKeyboardProps) {
  const { ref, value, setValue, insert, backspace } = useKeyboardText();
  const [lang, setLang] = useState<Lang>("yo");
  const [mode, setMode] = useState<Mode>("abc");
  const [shiftOn, setShiftOn] = useState(false);
  const [tone, setTone] = useState<TonePopover | null>(null);

  const wrapRef = useRef<HTMLDivElement | null>(null);
  const suppress = useRef<string | null>(null);

  const clamp = useEdgeClamp(tone !== null);
  useDismissOnOutsidePointer(tone !== null, () => setTone(null));

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

  const display = useMemo(
    () => ({
      "{shift}": "⇧",
      "{bksp}": "⌫",
      "{enter}": "↵",
      "{space}": lang === "yo" ? "àyè" : "space",
      "{num}": "123",
      "{abc}": "ABC",
    }),
    [lang],
  );

  const buttonTheme = useMemo(() => {
    const themes: { class: string; buttons: string }[] = [
      { class: "kbd-mod", buttons: "{shift} {bksp} {num} {abc}" },
      { class: "kbd-enter", buttons: "{enter}" },
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
    <div className="mx-auto w-full max-w-[420px]">
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={2}
        aria-label="Yoruba keyboard text input"
        placeholder={lang === "yo" ? "Bẹ̀rẹ̀ sí kọ…" : "Start typing…"}
        className="w-full resize-none rounded-xl border border-brand-brown/15 bg-white p-3 text-[15px] text-brand-ink outline-none placeholder:text-brand-brown/40 focus:border-brand-forest"
      />

      <div className="mt-3 flex justify-center gap-2">
        {langPill("yo", "Yorùbá")}
        {langPill("en", "English")}
      </div>

      <div
        ref={wrapRef}
        data-clip
        onContextMenu={(e) => e.preventDefault()}
        className="relative mt-3 touch-manipulation select-none overflow-hidden rounded-2xl border border-brand-brown/10 bg-brand-beige/50 px-3 py-3"
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
                  onClick={() => {
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

      <p className="mt-3 text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-brown/45">
        {lang === "yo"
          ? "Yorùbá mode · long-press a dotted key for tones"
          : "English mode"}
      </p>

      <CopyClearBar value={value} onClear={() => setValue("")} />
    </div>
  );
}
