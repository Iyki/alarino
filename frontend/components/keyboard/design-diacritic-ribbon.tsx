"use client";

import { useCallback, useState } from "react";

import { CopyClearBar, useKeyboardText } from "./keyboard-chrome";
import { pickAlign, popoverAlignClass, type PopoverAlign } from "./popover-align";
import { hasTones, toneVariants } from "./tones";
import { useDismissOnOutsidePointer, useLongPress } from "./use-long-press";

// Desktop "ribbon": a compact strip of just the Yoruba-specific glyphs
// for someone already typing on a physical QWERTY keyboard. Groups are
// colour-coded; dotted keys long-press to a tone picker.
const SUBDOT = ["ẹ", "ọ", "ṣ", "gb"];
const VOWELS = ["a", "e", "i", "o", "u"];
const NASALS = ["m", "n"];

interface RibbonKeyProps {
  base: string;
  align: PopoverAlign;
  accent: string;
  shiftOn: boolean;
  openId: string | null;
  setOpenId: (id: string | null) => void;
  onInsert: (text: string) => void;
}

function RibbonKey({
  base,
  align,
  accent,
  shiftOn,
  openId,
  setOpenId,
  onInsert,
}: RibbonKeyProps) {
  const id = base;
  const toneable = hasTones(base);
  const variants = toneable ? toneVariants(base) : null;
  const open = openId === id;
  const display = shiftOn ? base.toUpperCase() : base;

  const { start, cancel, wasTriggered } = useLongPress(() => {
    if (toneable) setOpenId(id);
  });

  const handleUp = useCallback(() => {
    if (!wasTriggered()) onInsert(shiftOn ? base.toUpperCase() : base);
    cancel();
  }, [wasTriggered, onInsert, base, shiftOn, cancel]);

  return (
    <div className="relative" data-picker-root={open ? "" : undefined}>
      <button
        type="button"
        onPointerDown={start}
        onPointerUp={handleUp}
        onPointerLeave={cancel}
        onPointerCancel={cancel}
        className={`relative flex h-12 w-12 select-none items-center justify-center rounded-lg border bg-white text-lg font-semibold text-brand-ink transition hover:-translate-y-0.5 hover:shadow-card active:translate-y-0 ${accent}`}
      >
        {display}
        {toneable ? (
          <span className="absolute right-1.5 top-1.5 h-1 w-1 rounded-full bg-current opacity-50" />
        ) : null}
      </button>
      {open && variants ? (
        <div
          className={`absolute -top-14 z-10 flex gap-1 whitespace-nowrap rounded-xl border border-brand-brown/15 bg-white px-1.5 py-1 shadow-card-hover ${popoverAlignClass(align)}`}
        >
          {variants.map((v) => {
            const out = shiftOn ? v.toUpperCase() : v;
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

export function DesignDiacriticRibbon() {
  const { ref, value, setValue, insert } = useKeyboardText();
  const [shiftOn, setShiftOn] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);

  useDismissOnOutsidePointer(openId !== null, () => setOpenId(null));

  const group = (keys: string[], accent: string) =>
    keys.map((base, i) => (
      <RibbonKey
        key={base}
        base={base}
        align={pickAlign(i, keys.length)}
        accent={accent}
        shiftOn={shiftOn}
        openId={openId}
        setOpenId={setOpenId}
        onInsert={insert}
      />
    ));

  return (
    <div>
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={4}
        placeholder="Type with your hardware keyboard; tap the ribbon for Yoruba glyphs and hold a dotted key for tones."
        className="w-full resize-none rounded-xl border border-brand-brown/15 bg-brand-cream p-4 text-base text-brand-ink outline-none focus:border-brand-forest"
      />

      <div className="mt-4 flex flex-wrap items-center gap-3 overflow-hidden rounded-2xl bg-brand-beige/60 p-3">
        <button
          type="button"
          onClick={() => setShiftOn((s) => !s)}
          className={`flex h-12 items-center justify-center rounded-lg border px-4 text-sm font-semibold transition ${
            shiftOn
              ? "border-brand-forest bg-brand-forest text-white"
              : "border-brand-brown/15 bg-white text-brand-ink"
          }`}
        >
          ⇧ {shiftOn ? "ABC" : "abc"}
        </button>

        <div className="flex gap-1.5 text-brand-forest">{group(SUBDOT, "border-brand-forest/30")}</div>
        <span className="h-8 w-px bg-brand-brown/15" />
        <div className="flex gap-1.5 text-brand-gold">{group(VOWELS, "border-brand-gold/40")}</div>
        <span className="h-8 w-px bg-brand-brown/15" />
        <div className="flex gap-1.5 text-brand-terracotta">{group(NASALS, "border-brand-terracotta/40")}</div>
      </div>

      <CopyClearBar value={value} onClear={() => setValue("")} />
    </div>
  );
}
