"use client";

import { useCallback, useRef, useState, type ReactNode } from "react";

// Shared textarea state + insert-at-cursor. Keeps the caret stable so
// successive key/tone presses build a continuous string.
export function useKeyboardText() {
  const ref = useRef<HTMLTextAreaElement | null>(null);
  const [value, setValue] = useState("");

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
  }, [value]);

  const backspace = useCallback(() => {
    const el = ref.current;
    if (!el) {
      setValue((prev) => prev.slice(0, -1));
      return;
    }
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    if (start === end && start === 0) return;
    const from = start === end ? start - 1 : start;
    const next = value.slice(0, from) + value.slice(end);
    setValue(next);
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(from, from);
    });
  }, [value]);

  return { ref, value, setValue, insert, backspace };
}

interface DesignSectionProps {
  title: string;
  badge: string;
  blurb: string;
  children: ReactNode;
}

export function DesignSection({ title, badge, blurb, children }: DesignSectionProps) {
  return (
    <section className="mb-7 rounded-3xl border border-brand-brown/10 bg-white p-6 shadow-card md:p-8">
      <div className="mb-5 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="font-heading text-2xl font-extrabold text-brand-ink">{title}</h2>
        <span className="rounded-full bg-brand-forest-light px-2.5 py-0.5 text-xs font-semibold text-brand-forest">
          {badge}
        </span>
      </div>
      <p className="mb-5 max-w-2xl text-sm leading-relaxed text-brand-brown/80">{blurb}</p>
      {children}
    </section>
  );
}

interface CopyClearBarProps {
  value: string;
  onClear: () => void;
}

export function CopyClearBar({ value, onClear }: CopyClearBarProps) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }, [value]);

  return (
    <div className="mt-3 flex items-center justify-between text-xs text-brand-brown/70">
      <span>{value.length} character{value.length === 1 ? "" : "s"}</span>
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
