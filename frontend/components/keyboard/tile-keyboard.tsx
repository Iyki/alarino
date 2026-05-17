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
        className="relative flex h-12 w-full select-none items-center justify-center rounded-lg border border-brand-brown/15 bg-brand-cream text-base font-semibold text-brand-ink transition active:scale-95 active:bg-brand-gold-light"
      >
        {display}
        {toneable ? (
          <span className="absolute right-1 top-1 h-1 w-1 rounded-full bg-brand-gold" />
        ) : null}
      </button>
      {open && variants ? (
        <div
          ref={clamp.ref}
          style={clamp.style}
          className={`absolute -top-14 z-10 flex gap-1 whitespace-nowrap rounded-xl border border-brand-brown/15 bg-white px-1.5 py-1 shadow-card-hover ${popoverAlignClass(align)}`}
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
                className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-cream text-lg font-semibold text-brand-ink transition hover:bg-brand-gold-light"
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

  const langPill = (target: Lang, label: string, activeClass: string) => (
    <button
      type="button"
      onClick={() => {
        setLang(target);
        setOpenId(null);
      }}
      className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${
        lang === target ? activeClass : "bg-brand-beige text-brand-brown/70"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="mx-auto max-w-md">
      <div className="mb-3 flex gap-2">
        {langPill("yo", "Yorùbá", "bg-brand-forest text-white")}
        {langPill("en", "English", "bg-brand-indigo text-white")}
      </div>

      <textarea
        ref={ref}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={3}
        placeholder={lang === "yo" ? "Kọ ní èdè Yorùbá…" : "Type here…"}
        className="w-full resize-none rounded-xl border border-brand-brown/15 bg-brand-cream p-3 text-base text-brand-ink outline-none focus:border-brand-forest"
      />

      <div
        data-clip
        className="mt-3 space-y-1.5 overflow-hidden rounded-xl bg-brand-beige/60 p-2"
      >
        {[rows[0], rows[1]].map((row, rIdx) => (
          <div key={`r${rIdx}`} className="flex gap-1">
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

        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => setShiftOn((s) => !s)}
            style={modStyle}
            className={`flex h-12 select-none items-center justify-center rounded-lg border text-sm font-semibold transition ${
              shiftOn
                ? "border-brand-forest bg-brand-forest text-white"
                : "border-brand-brown/15 bg-brand-cream text-brand-ink"
            }`}
          >
            ⇧
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
            className="flex h-12 select-none items-center justify-center rounded-lg border border-brand-brown/15 bg-brand-cream text-sm font-semibold text-brand-ink transition active:scale-95"
          >
            ⌫
          </button>
        </div>

        <div className="flex gap-1 pt-0.5">
          <button
            type="button"
            onClick={() => insert(" ")}
            className="h-12 flex-1 select-none rounded-lg border border-brand-brown/15 bg-brand-cream text-sm font-semibold text-brand-brown/70 transition active:scale-95"
          >
            {lang === "yo" ? "àlàfo" : "space"}
          </button>
          <button
            type="button"
            onClick={() => insert("\n")}
            style={modStyle}
            className="flex h-12 select-none items-center justify-center rounded-lg border border-brand-brown/15 bg-brand-cream text-sm font-semibold text-brand-ink transition active:scale-95"
          >
            ↵
          </button>
        </div>
      </div>

      <CopyClearBar value={value} onClear={() => setValue("")} />
    </div>
  );
}
