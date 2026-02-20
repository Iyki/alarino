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
      className={`mt-12 rounded-3xl bg-brand-beige p-4 shadow-card transition sm:p-6 ${
        isHighlighted ? "ring-4 ring-brand-gold/80" : "ring-0"
      }`}
    >
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
          className="w-full rounded-xl border border-brand-brown/20 bg-white px-4 py-3 text-brand-ink placeholder:text-brand-ink/55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        />
        <button
          type="submit"
          aria-busy={translationState.loading}
          className="rounded-xl bg-brand-forest px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
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

      <div className="mt-4 rounded-2xl bg-white p-5">
        {translationState.loading ? (
          <p role="status" aria-live="polite" className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-brand-ink/80">
            <span
              aria-hidden="true"
              className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-brown/25 border-t-brand-forest"
            />
            Looking up translation...
          </p>
        ) : null}
        <p className="text-xl font-semibold text-brand-ink">
          {translationState.word}
          <span className="ml-2 text-sm font-normal text-brand-ink/65">
            {translationState.word === DEFAULT_TRANSLATION_WORD ? "(example)" : "(English)"}
          </span>
        </p>
        <div className="mt-2 space-y-1 text-lg italic text-brand-ink/85">
          {translationMarkup.map((line, index) => (
            <p key={`${line}-${index}`}>{line}</p>
          ))}
        </div>
        {translationState.description ? (
          <p className="mt-3 text-sm text-brand-ink/70">{translationState.description}</p>
        ) : null}
      </div>
    </section>
  );
}
