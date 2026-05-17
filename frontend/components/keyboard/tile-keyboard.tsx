"use client";

import { useCallback, useState, type CSSProperties } from "react";

import { CopyClearBar, useKeyboardText } from "./keyboard-chrome";
import { pickAlign, popoverAlignClass } from "./popover-align";
import { hasTones, toneVariants } from "./tones";
import { useDismissOnOutsidePointer, useEdgeClamp, useLongPress } from "./use-long-press";

export type KeyRows = [string[], string[], string[]];

export interface ModeToggleKeyboardProps {
  yoRows: KeyRows;
  enRows: KeyRows;
  letterStyle: CSSProperties;
  modStyle: CSSProperties;
}

type Lang = "yo" | "en";

function applyShift(text: string, shiftOn: boolean): string {
  return shiftOn ? text.toUpperCase() : text;
}

// Yoruba-specific glyphs (the dotted vowels, ṣ, and the gb digraph) get a
// faint forest tint so they stand out from the shared QWERTY letters.
function isSpecial(base: string): boolean {
  return base.length > 1 || /[^a-z]/.test(base);
}

const ICON = "h-[18px] w-[18px]";

function ShiftIcon({ filled }: { filled: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className={ICON} fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round">
      <path d="M12 3 4 11h4v7h8v-7h4z" />
    </svg>
  );
}

function BackspaceIcon() {
  return (
    <svg viewBox="0 0 24 24" className={ICON} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 5h11v14H9L3 12z" />
      <path d="m12 9 5 6m0-6-5 6" />
    </svg>
  );
}

function ReturnIcon() {
  return (
    <svg viewBox="0 0 24 24" className={ICON} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6v5a3 3 0 0 1-3 3H5" />
      <path d="m9 10-4 4 4 4" />
    </svg>
  );
}

function GlobeIcon() {
  return (
    <svg viewBox="0 0 24 24" className={ICON} fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" />
    </svg>
  );
}

const KEY_BASE =
  "relative flex h-[42px] select-none items-center justify-center rounded-lg border text-[17px] transition active:scale-95";
const LETTER_KEY = "w-full border-brand-brown/15 bg-white text-brand-ink active:bg-brand-gold-light";
const SPECIAL_KEY = "w-full border-brand-forest/25 bg-brand-forest-light text-brand-forest active:bg-brand-forest/15";
const MOD_KEY = "border-brand-brown/15 bg-brand-beige text-brand-brown/70 active:bg-brand-brown/10";

interface TileKeyProps {
  base: string;
  rowIndex: number;
  rowLength: number;
  lang: Lang;
  shiftOn: boolean;
  openId: string | null;
  setOpenId: (id: string | null) => void;
  onInsert: (text: string) => void;
  letterStyle: CSSProperties;
}

function TileKey({
  base,
  rowIndex,
  rowLength,
  lang,
  shiftOn,
  openId,
  setOpenId,
  onInsert,
  letterStyle,
}: TileKeyProps) {
  const id = `${lang}-${rowIndex}-${base}`;
  const toneable = lang === "yo" && hasTones(base);
  const variants = toneable ? toneVariants(base) : null;
  const open = openId === id;

  const { start, cancel, wasTriggered } = useLongPress(() => {
    if (toneable) setOpenId(id);
  });

  const display = applyShift(base, shiftOn);
  const align = pickAlign(rowIndex, rowLength);
  const clamp = useEdgeClamp(open);
  const special = lang === "yo" && isSpecial(base);

  const handleUp = useCallback(() => {
    if (!wasTriggered()) onInsert(applyShift(base, shiftOn));
    cancel();
  }, [wasTriggered, onInsert, base, shiftOn, cancel]);

  return (
    <div className="relative" style={letterStyle} data-picker-root={open ? "" : undefined}>
      <button
        type="button"
        onPointerDown={start}
        onPointerUp={handleUp}
        onPointerLeave={cancel}
        onPointerCancel={cancel}
        className={`${KEY_BASE} ${special ? SPECIAL_KEY : LETTER_KEY} ${open ? "ring-2 ring-brand-forest/40" : ""}`}
      >
        {display}
        {toneable ? (
          <span className="absolute right-[5px] top-[4px] h-[3px] w-[3px] rounded-full bg-brand-gold" />
        ) : null}
      </button>
      {open && variants ? (
        <div
          ref={clamp.ref}
          style={clamp.style}
          className={`absolute -top-[54px] z-20 flex gap-1 whitespace-nowrap rounded-xl border border-brand-brown/15 bg-white px-1.5 py-1 shadow-card-hover ${popoverAlignClass(align)}`}
        >
          {variants.map((v) => {
            const out = applyShift(v, shiftOn);
            return (
              <button
                key={v}
                type="button"
                onPointerDown={(e) => {
                  e.stopPropagation();
                  onInsert(out);
                  setOpenId(null);
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
  );
}

export function ModeToggleKeyboard({
  yoRows,
  enRows,
  letterStyle,
  modStyle,
}: ModeToggleKeyboardProps) {
  const { ref, value, setValue, insert, backspace } = useKeyboardText();
  const [lang, setLang] = useState<Lang>("yo");
  const [shiftOn, setShiftOn] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);

  useDismissOnOutsidePointer(openId !== null, () => setOpenId(null));

  const rows = lang === "yo" ? yoRows : enRows;

  const switchLang = (target: Lang) => {
    setLang(target);
    setOpenId(null);
  };

  const langPill = (target: Lang, label: string) => (
    <button
      type="button"
      onClick={() => switchLang(target)}
      className={`rounded-full px-4 py-1 text-[13px] font-semibold transition ${
        lang === target
          ? "bg-brand-forest text-white shadow-card"
          : "border border-brand-brown/15 bg-white text-brand-brown/60"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="mx-auto w-full max-w-[420px]">
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={2}
        placeholder={lang === "yo" ? "Bẹ̀rẹ̀ sí kọ…" : "Start typing…"}
        className="w-full resize-none rounded-xl border border-brand-brown/15 bg-white p-3 text-[15px] text-brand-ink outline-none placeholder:text-brand-brown/40 focus:border-brand-forest"
      />

      <div className="mt-3 flex justify-center gap-2">
        {langPill("yo", "Yorùbá")}
        {langPill("en", "English")}
      </div>

      <div
        data-clip
        className="mt-3 space-y-[6px] overflow-hidden rounded-2xl border border-brand-brown/10 bg-brand-beige/50 p-2"
      >
        {[rows[0], rows[1]].map((row, rIdx) => (
          <div key={`r${rIdx}`} className="flex gap-1 px-0.5">
            {row.map((base, i) => (
              <TileKey
                key={`${base}-${i}`}
                base={base}
                rowIndex={i}
                rowLength={row.length}
                lang={lang}
                shiftOn={shiftOn}
                openId={openId}
                setOpenId={setOpenId}
                onInsert={insert}
                letterStyle={letterStyle}
              />
            ))}
          </div>
        ))}

        <div className="flex gap-1 px-0.5">
          <button
            type="button"
            onClick={() => setShiftOn((s) => !s)}
            style={modStyle}
            className={`${KEY_BASE} ${
              shiftOn
                ? "border-brand-forest bg-brand-forest text-white"
                : MOD_KEY
            }`}
            aria-label="Shift"
          >
            <ShiftIcon filled={shiftOn} />
          </button>
          {rows[2].map((base, i) => (
            <TileKey
              key={`${base}-${i}`}
              base={base}
              rowIndex={i + 1}
              rowLength={rows[2].length + 2}
              lang={lang}
              shiftOn={shiftOn}
              openId={openId}
              setOpenId={setOpenId}
              onInsert={insert}
              letterStyle={letterStyle}
            />
          ))}
          <button
            type="button"
            onClick={backspace}
            style={modStyle}
            className={`${KEY_BASE} ${MOD_KEY} ml-auto`}
            aria-label="Backspace"
          >
            <BackspaceIcon />
          </button>
        </div>

        <div className="flex gap-1 px-0.5">
          <button
            type="button"
            onClick={() => switchLang(lang === "yo" ? "en" : "yo")}
            style={modStyle}
            className={`${KEY_BASE} ${MOD_KEY}`}
            aria-label="Switch language"
          >
            <GlobeIcon />
          </button>
          <button
            type="button"
            onClick={() => insert(" ")}
            style={{ flex: "5 5 0%", minWidth: 0 }}
            className={`${KEY_BASE} ${LETTER_KEY} text-[12px] font-semibold uppercase tracking-[0.2em] text-brand-brown/50`}
          >
            {lang === "yo" ? "àlàfo" : "space"}
          </button>
          <button
            type="button"
            onClick={() => insert("\n")}
            style={modStyle}
            className={`${KEY_BASE} border-brand-forest bg-brand-forest text-white active:bg-brand-forest/80`}
            aria-label="Return"
          >
            <ReturnIcon />
          </button>
        </div>
      </div>

      <p className="mt-3 text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-brown/45">
        {lang === "yo"
          ? "Yorùbá mode · long-press a dotted key for tones"
          : "English mode · standard QWERTY"}
      </p>

      <CopyClearBar value={value} onClear={() => setValue("")} />
    </div>
  );
}
