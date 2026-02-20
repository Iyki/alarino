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
    <main className="mx-auto w-full max-w-6xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
      <section className="text-center">
        <p className="font-heading text-sm uppercase tracking-[0.2em] text-brand-cream/85">English to Yoruba Dictionary</p>
        <h1 className="mt-5 font-heading text-4xl text-white sm:text-5xl">Discover words in Yoruba</h1>
        <button
          type="button"
          onClick={focusTranslator}
          className="mt-8 rounded-xl bg-brand-forest px-6 py-3 text-sm font-semibold text-white shadow-card transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          Start Translating
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

      <section className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-3">
        <WordOfDayCard
          dailyWord={dailyWord}
          isTranslationVisible={isDailyTranslationVisible}
          onToggleTranslation={toggleDailyTranslation}
        />
        <ProverbCard
          proverb={proverb}
          loading={proverbLoading}
          onNextProverb={() => {
            void loadRandomProverb();
          }}
        />
        <SuggestionsCard
          onOpenModal={(modal) => {
            setActiveModal(modal);
          }}
        />
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
