import { RefObject, useMemo } from "react";

import { DEFAULT_TRANSLATION_WORD } from "@/lib/constants";
import type { TranslationViewState } from "@/components/home/use-home-page-state";

interface TranslatorCardProps {
  input: string;
  isHighlighted: boolean;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  translationState: TranslationViewState;
  translateCardRef: RefObject<HTMLElement | null>;
}

export function TranslatorCard({
  input,
  isHighlighted,
  onInputChange,
  onSubmit,
  translationState,
  translateCardRef
}: TranslatorCardProps) {
  const translationMarkup = useMemo(
    () => translationState.translation.map((line) => line.trim()).filter(Boolean),
    [translationState.translation]
  );

  return (
    <section
      ref={translateCardRef}
      className={`mt-12 overflow-hidden rounded-3xl bg-brand-cream shadow-card transition-all duration-300 ${
        isHighlighted ? "ring-4 ring-brand-gold/80 shadow-card-hover" : "ring-0"
      }`}
    >
      <div className="border-b border-brand-brown/10 p-4 sm:p-6">
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-ink/50">English</p>
        <form
          className="flex flex-col gap-3 sm:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
          }}
        >
          <label htmlFor="englishWord" className="sr-only">
            Enter an English word
          </label>
          <input
            id="englishWord"
            name="englishWord"
            type="text"
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            placeholder="Enter an English word..."
            className="w-full rounded-xl border border-brand-brown/15 bg-white px-4 py-3 text-brand-ink shadow-sm placeholder:text-brand-ink/40 transition-shadow focus-visible:outline-none focus-visible:shadow-md focus-visible:ring-2 focus-visible:ring-brand-forest"
          />
          <button
            type="submit"
            aria-busy={translationState.loading}
            className="rounded-xl bg-brand-forest px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand-forest/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold focus-visible:ring-offset-2"
          >
            {translationState.loading ? (
              <span className="inline-flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/35 border-t-white"
                />
                <span>Translating...</span>
              </span>
            ) : (
              "Translate"
            )}
          </button>
        </form>
      </div>

      <div className="p-4 sm:p-6">
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-ink/50">Yoruba</p>
        <div className="rounded-2xl bg-white p-5 shadow-sm">
          {translationState.loading ? (
            <p role="status" aria-live="polite" className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-brand-ink/70">
              <span
                aria-hidden="true"
                className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-brown/25 border-t-brand-forest"
              />
              Looking up translation...
            </p>
          ) : null}
          <p className="font-heading text-xl font-semibold text-brand-ink">
            {translationState.word}
            <span className="ml-2 font-body text-sm font-normal text-brand-ink/50">
              {translationState.word === DEFAULT_TRANSLATION_WORD ? "(example)" : "(English)"}
            </span>
          </p>
          <div className="mt-2 space-y-1 text-lg font-medium text-brand-forest">
            {translationMarkup.map((line, index) => (
              <p key={`${line}-${index}`}>{line}</p>
            ))}
          </div>
          {translationState.description ? (
            <p className="mt-3 text-sm text-brand-ink/60">{translationState.description}</p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
