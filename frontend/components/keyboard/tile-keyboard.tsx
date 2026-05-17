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

const ICON = "h-[22px] w-[22px]";

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
  "relative flex select-none items-center justify-center rounded-[6px] text-[20px] leading-none transition-colors";
const LETTER_KEY =
  "h-[44px] w-full bg-white text-black shadow-[0_1px_0_rgba(0,0,0,0.28)] active:bg-[#e7e8eb]";
const MOD_KEY =
  "h-[44px] bg-[#aab0bb] text-[15px] font-medium text-black shadow-[0_1px_0_rgba(0,0,0,0.28)] active:bg-[#9197a3]";

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
        className={`${KEY_BASE} ${LETTER_KEY} ${open ? "bg-[#e7e8eb]" : ""}`}
      >
        {display}
        {toneable ? (
          <span className="absolute right-[5px] top-[5px] h-[3px] w-[3px] rounded-full bg-black/30" />
        ) : null}
      </button>
      {open && variants ? (
        <div
          ref={clamp.ref}
          style={clamp.style}
          className={`absolute -top-[58px] z-20 flex gap-1 whitespace-nowrap rounded-2xl bg-white p-1.5 shadow-[0_6px_20px_rgba(0,0,0,0.28)] ${popoverAlignClass(align)}`}
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
                className="flex h-11 w-11 items-center justify-center rounded-xl text-[24px] text-black transition-colors hover:bg-[#3478f6] hover:text-white active:bg-[#3478f6] active:text-white"
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

  return (
    <div className="mx-auto w-full max-w-[400px]">
      {/* Phone frame */}
      <div className="overflow-hidden rounded-[40px] border-[10px] border-black bg-black shadow-card-hover">
        {/* Screen */}
        <div className="flex h-[150px] flex-col bg-white">
          <div className="relative flex justify-center pt-2">
            <span className="h-1.5 w-20 rounded-full bg-black/15" />
          </div>
          <div className="flex flex-1 items-end px-3 pb-3">
            <textarea
              ref={ref}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              rows={2}
              placeholder={lang === "yo" ? "Kọ ọ̀rọ̀ Yorùbá…" : "Type a message…"}
              className="max-h-[90px] w-full resize-none rounded-[20px] border border-black/10 bg-[#f1f2f4] px-4 py-2.5 text-[15px] text-black outline-none placeholder:text-black/35 focus:border-black/20"
            />
          </div>
        </div>

        {/* Keyboard tray */}
        <div data-clip className="overflow-hidden bg-[#d1d4db] px-[3px] pb-[6px] pt-[8px]">
          {/* Predictive strip == language mode toggle */}
          <div className="mb-[8px] flex h-9 items-center overflow-hidden rounded-lg bg-white/55 text-[13px] font-semibold">
            {(["yo", "en"] as Lang[]).map((l, idx) => (
              <button
                key={l}
                type="button"
                onClick={() => switchLang(l)}
                className={`flex h-full flex-1 items-center justify-center transition-colors ${
                  idx === 0 ? "border-r border-black/10" : ""
                } ${
                  lang === l
                    ? l === "yo"
                      ? "bg-brand-forest text-white"
                      : "bg-brand-indigo text-white"
                    : "text-black/55"
                }`}
              >
                {l === "yo" ? "Yorùbá" : "English"}
              </button>
            ))}
          </div>

          <div className="space-y-[10px]">
            {[rows[0], rows[1]].map((row, rIdx) => (
              <div key={`r${rIdx}`} className="flex gap-[6px] px-[2px]">
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

            <div className="flex gap-[6px] px-[2px]">
              <button
                type="button"
                onClick={() => setShiftOn((s) => !s)}
                style={modStyle}
                className={`${KEY_BASE} ${MOD_KEY} ${
                  shiftOn ? "!bg-white !text-black" : ""
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

            <div className="flex gap-[6px] px-[2px]">
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
                className={`${KEY_BASE} ${LETTER_KEY} text-[14px] font-medium text-black/50`}
              >
                {lang === "yo" ? "àlàfo" : "space"}
              </button>
              <button
                type="button"
                onClick={() => insert("\n")}
                style={modStyle}
                className={`${KEY_BASE} ${MOD_KEY} gap-1.5 text-[14px]`}
                aria-label="Return"
              >
                <ReturnIcon />
              </button>
            </div>
          </div>
        </div>
      </div>

      <CopyClearBar value={value} onClear={() => setValue("")} />
    </div>
  );
}
