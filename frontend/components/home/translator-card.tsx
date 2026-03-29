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
  const experimentalMarkup = useMemo(
    () => translationState.experimentalTranslation.map((line) => line.trim()).filter(Boolean),
    [translationState.experimentalTranslation]
  );

  return (
    <section
      ref={translateCardRef}
      className={`h-full overflow-hidden rounded-[1.25rem] border border-brand-brown/[0.06] bg-brand-cream shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card-hover ${
        isHighlighted ? "ring-4 ring-brand-gold/80" : ""
      }`}
    >
      <div className="p-6 md:p-8">
        <div className="grid grid-cols-1 md:grid-cols-2">
          {/* English input pane */}
          <div className="border-b border-brand-brown/[0.08] pb-6 md:border-b-0 md:border-r md:pb-0 md:pr-6">
            <p className="mb-4 flex items-center gap-1.5 text-[0.7rem] font-bold uppercase tracking-[0.15em] text-brand-ink/40">
              <span className="h-1.5 w-1.5 rounded-full bg-brand-brown" />
              English
            </p>
            <form
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
                placeholder="Type a word..."
                className="w-full border-none bg-transparent font-heading text-2xl font-semibold text-brand-ink outline-none placeholder:text-brand-ink/25"
              />
              <button
                type="submit"
                aria-busy={translationState.loading}
                className="mt-5 rounded-xl bg-brand-forest px-6 py-3 text-sm font-semibold text-white shadow-[0_1px_4px_rgba(26,92,50,0.2)] transition-all duration-200 hover:-translate-y-px hover:bg-[#227a42] hover:shadow-[0_3px_10px_rgba(26,92,50,0.25)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
              >
                {translationState.loading ? (
                  <span className="inline-flex items-center gap-2">
                    <span
                      aria-hidden="true"
                      className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/35 border-t-white"
                    />
                    Translating...
                  </span>
                ) : (
                  "Translate"
                )}
              </button>
            </form>
          </div>

          {/* Yoruba output pane */}
          <div className="pt-6 md:pl-6 md:pt-0">
            <p className="mb-4 flex items-center gap-1.5 text-[0.7rem] font-bold uppercase tracking-[0.15em] text-brand-ink/40">
              <span className="h-1.5 w-1.5 rounded-full bg-brand-forest" />
              Yoruba
            </p>
            {translationState.loading ? (
              <p role="status" aria-live="polite" className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-brand-ink/70">
                <span
                  aria-hidden="true"
                  className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-brown/25 border-t-brand-forest"
                />
                Looking up translation...
              </p>
            ) : null}
            <p className="font-heading text-2xl font-semibold text-brand-ink">
              {translationState.word}
              <span className="ml-2 font-body text-xs text-brand-ink/35">
                {translationState.word === DEFAULT_TRANSLATION_WORD ? "(example)" : "(English)"}
              </span>
            </p>
            {translationState.error ? (
              <div className="mt-3 rounded-lg border-l-[3px] border-brand-gold bg-brand-gold-light px-3 py-2 text-sm text-brand-brown">
                {translationState.description || "Translation not found. Try another word."}
              </div>
            ) : (
              <>
                <div className="mt-2 space-y-1 text-xl font-semibold text-brand-forest">
                  {translationMarkup.map((line, index) => (
                    <p key={`${line}-${index}`}>{line}</p>
                  ))}
                </div>
                {experimentalMarkup.length > 0 ? (
                  <section className="mt-5 rounded-xl border border-brand-brown/[0.08] bg-white/75 px-4 py-3">
                    <p className="text-[0.7rem] font-bold uppercase tracking-[0.15em] text-brand-brown/60">
                      Experimental
                    </p>
                    <div className="mt-2 space-y-1 text-lg font-semibold text-brand-brown">
                      {experimentalMarkup.map((line, index) => (
                        <p key={`${line}-experimental-${index}`}>{line}</p>
                      ))}
                    </div>
                  </section>
                ) : null}
                {translationState.description ? (
                  <p className="mt-3 text-sm text-brand-ink/60">{translationState.description}</p>
                ) : null}
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
