"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { ContributionModal } from "@/components/home/contribution-modal";
import { ProverbCard } from "@/components/home/proverb-card";
import { SuggestionsCard } from "@/components/home/suggestions-card";
import { TranslatorCard } from "@/components/home/translator-card";
import { useHomePageState } from "@/components/home/use-home-page-state";
import { WordOfDayCard } from "@/components/home/word-of-day-card";

interface HomePageProps {
  initialWord?: string;
}

export function HomePage({ initialWord }: HomePageProps) {
  const router = useRouter();
  const pathname = usePathname();
  const translateCardRef = useRef<HTMLElement>(null);
  const [isTranslateCardHighlighted, setIsTranslateCardHighlighted] = useState(false);

  const onTranslatedWord = useCallback(
    (translatedWord: string) => {
      const targetPath = `/word/${encodeURIComponent(translatedWord)}`;
      if (pathname !== targetPath) {
        router.replace(targetPath, { scroll: false });
      }
    },
    [pathname, router]
  );

  const {
    activeModal,
    dailyWord,
    input,
    isDailyTranslationVisible,
    proverb,
    proverbLoading,
    setActiveModal,
    setInput,
    submitTranslation,
    toggleDailyTranslation,
    translationState,
    loadRandomProverb
  } = useHomePageState({ initialWord, onTranslatedWord });

  const pulseTranslateCard = useCallback(() => {
    setIsTranslateCardHighlighted(true);
    window.setTimeout(() => setIsTranslateCardHighlighted(false), 1600);
  }, []);

  const focusTranslator = useCallback(() => {
    translateCardRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    pulseTranslateCard();
  }, [pulseTranslateCard]);

  useEffect(() => {
    if (!initialWord) {
      return;
    }

    focusTranslator();
  }, [focusTranslator, initialWord]);

  useEffect(() => {
    if (!activeModal) {
      document.body.classList.remove("overflow-hidden");
      return;
    }

    document.body.classList.add("overflow-hidden");

    return () => {
      document.body.classList.remove("overflow-hidden");
    };
  }, [activeModal]);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-20 pt-12 sm:px-6 lg:px-8">
      <section className="animate-fade-in-up text-center">
        <p className="text-sm font-medium uppercase tracking-[0.25em] text-brand-gold">English to Yoruba Dictionary</p>
        <h1 className="mt-4 font-heading text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
          Discover words in <span className="text-brand-gold">Yoruba</span>
        </h1>
        <p className="mx-auto mt-4 max-w-lg text-base text-brand-cream/75 sm:text-lg">
          Explore translations, proverbs, and daily words from the Yoruba language
        </p>
        <button
          type="button"
          onClick={focusTranslator}
          className="mt-8 inline-flex items-center gap-2 rounded-xl bg-brand-forest px-7 py-3.5 text-sm font-semibold text-white shadow-lg transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand-forest/90 hover:shadow-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold focus-visible:ring-offset-2 focus-visible:ring-offset-brand-brown"
        >
          Start Translating
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </button>
      </section>

      <TranslatorCard
        input={input}
        isHighlighted={isTranslateCardHighlighted}
        onInputChange={setInput}
        onSubmit={() => {
          void submitTranslation(input);
        }}
        translationState={translationState}
        translateCardRef={translateCardRef}
      />

      <section className="mt-10 grid grid-cols-1 gap-5 md:grid-cols-3">
        <div className="animate-fade-in-up">
          <WordOfDayCard
            dailyWord={dailyWord}
            isTranslationVisible={isDailyTranslationVisible}
            onToggleTranslation={toggleDailyTranslation}
          />
        </div>
        <div className="animate-fade-in-up-delay-1">
          <ProverbCard
            proverb={proverb}
            loading={proverbLoading}
            onNextProverb={() => {
              void loadRandomProverb();
            }}
          />
        </div>
        <div className="animate-fade-in-up-delay-2">
          <SuggestionsCard
            onOpenModal={(modal) => {
              setActiveModal(modal);
            }}
          />
        </div>
      </section>

      <ContributionModal
        activeModal={activeModal}
        onClose={() => {
          setActiveModal(null);
        }}
      />
    </main>
  );
}
