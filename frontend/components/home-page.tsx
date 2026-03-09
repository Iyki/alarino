"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

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
  const pathname = usePathname();
  const pathnameRef = useRef(pathname);
  pathnameRef.current = pathname;
  const translateCardRef = useRef<HTMLElement>(null);
  const [isTranslateCardHighlighted, setIsTranslateCardHighlighted] = useState(false);

  const onTranslatedWord = useCallback(
    (translatedWord: string) => {
      const targetPath = `/word/${encodeURIComponent(translatedWord)}`;
      if (pathnameRef.current !== targetPath) {
        window.history.replaceState(null, "", targetPath);
      }
    },
    []
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
    <main className="mx-auto w-full max-w-[80rem] px-6 py-8">
      {/* Hero Banner */}
      <div className="animate-fade-in-up relative mb-5 overflow-hidden rounded-3xl bg-gradient-to-br from-brand-brown to-[#2a1a0e] px-8 py-10 md:px-12">
        <div
          className="pointer-events-none absolute -right-8 -top-8 h-64 w-64 rounded-full"
          style={{ background: "radial-gradient(circle, rgba(200,149,46,0.2) 0%, transparent 70%)" }}
        />
        <div
          className="pointer-events-none absolute -bottom-12 left-[10%] h-48 w-48 rounded-full"
          style={{ background: "radial-gradient(circle, rgba(26,92,50,0.15) 0%, transparent 70%)" }}
        />
        <Link href="/" className="relative z-10 mb-7 inline-flex items-center gap-2.5">
          <Image
            src="/alarino_logo_only.svg"
            alt="Alarino logo"
            width={32}
            height={32}
            priority
            className="brightness-0 invert"
          />
          <span className="font-heading text-xl font-extrabold tracking-tight text-white">Alarino</span>
        </Link>
        <h1 className="relative z-10 font-heading text-[clamp(2rem,4vw,3rem)] font-extrabold leading-[1.15] text-white">
          Discover words<br />in Yoruba
        </h1>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-12">
        <div className="animate-fade-in-up-delay-1 md:col-span-8">
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
        </div>
        <div className="animate-fade-in-up-delay-2 md:col-span-4">
          <WordOfDayCard
            dailyWord={dailyWord}
            isTranslationVisible={isDailyTranslationVisible}
            onToggleTranslation={toggleDailyTranslation}
          />
        </div>
        <div className="animate-fade-in-up-delay-3 md:col-span-7">
          <ProverbCard
            proverb={proverb}
            loading={proverbLoading}
            onNextProverb={() => {
              void loadRandomProverb();
            }}
          />
        </div>
        <div className="animate-fade-in-up-delay-4 md:col-span-5">
          <SuggestionsCard
            onOpenModal={(modal) => {
              setActiveModal(modal);
            }}
          />
        </div>
      </div>

      <ContributionModal
        activeModal={activeModal}
        onClose={() => {
          setActiveModal(null);
        }}
      />
    </main>
  );
}
