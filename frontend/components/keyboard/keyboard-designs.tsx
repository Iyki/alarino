"use client";

import { useState } from "react";

import { DesignDiacriticRibbon } from "./design-diacritic-ribbon";
import { DesignTileModeToggleDvorak } from "./design-tile-mode-toggle-dvorak";
import { DesignTileModeToggleInlineB } from "./design-tile-mode-toggle-inline-b";
import { useMediaQuery } from "./use-media-query";

type MobileLayout = "qwerty" | "dvorak";

const MOBILE_LAYOUTS: { id: MobileLayout; label: string }[] = [
  { id: "qwerty", label: "QWERTY" },
  { id: "dvorak", label: "Dvorak" },
];

export function KeyboardDesigns() {
  // Desktop gets the hardware-keyboard ribbon; narrower viewports get a
  // touch keyboard. Gate on a real media query so each only renders where
  // it makes sense.
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const [layout, setLayout] = useState<MobileLayout>("qwerty");

  if (isDesktop === null) {
    return (
      <div
        aria-hidden
        className="min-h-[360px] animate-pulse rounded-2xl bg-brand-beige/40"
      />
    );
  }

  if (isDesktop) {
    return <DesignDiacriticRibbon />;
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-end gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-brown/45">
          Layout
        </span>
        <div className="inline-flex overflow-hidden rounded-full border border-brand-brown/15 bg-white">
          {MOBILE_LAYOUTS.map((m, i) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setLayout(m.id)}
              aria-pressed={layout === m.id}
              className={`px-3.5 py-1.5 text-[13px] font-semibold transition ${
                i === 0 ? "border-r border-brand-brown/10" : ""
              } ${
                layout === m.id
                  ? "bg-brand-forest text-white"
                  : "text-brand-brown/55"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {layout === "dvorak" ? (
        <DesignTileModeToggleDvorak />
      ) : (
        <DesignTileModeToggleInlineB />
      )}
    </div>
  );
}
