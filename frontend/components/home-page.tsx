"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { fetchDailyWord, fetchRandomProverb, translateEnglishWord } from "@/lib/api";

type ModalType = "add-word" | "feedback" | null;

type TranslationViewState = {
  word: string;
  translation: string[];
  description: string;
  loading: boolean;
};

interface HomePageProps {
  initialWord?: string;
}

const EMPTY_TRANSLATION_STATE: TranslationViewState = {
  word: "liaison",
  translation: ["alárìnọ̀ n."],
  description: "",
  loading: false
};

export function HomePage({ initialWord }: HomePageProps) {
  const router = useRouter();
  const pathname = usePathname();
  const translateCardRef = useRef<HTMLElement>(null);

  const [input, setInput] = useState(initialWord ?? "");
  const [translationState, setTranslationState] = useState<TranslationViewState>(EMPTY_TRANSLATION_STATE);

  const [dailyWord, setDailyWord] = useState({ yoruba: "ìfẹ́", english: "love" });
  const [isDailyTranslationVisible, setIsDailyTranslationVisible] = useState(false);

  const [proverb, setProverb] = useState({
    yoruba: "Bí ojú kò bá rí, ẹnu kì í sọ nǹkan.",
    english: "If the eye does not see, the mouth says nothing."
  });
  const [proverbLoading, setProverbLoading] = useState(false);

  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [isTranslateCardHighlighted, setIsTranslateCardHighlighted] = useState(false);

  const translationMarkup = useMemo(
    () => translationState.translation.map((line) => line.trim()).filter(Boolean),
    [translationState.translation]
  );

  const pulseTranslateCard = useCallback(() => {
    setIsTranslateCardHighlighted(true);
    window.setTimeout(() => setIsTranslateCardHighlighted(false), 1600);
  }, []);

  const focusTranslator = useCallback(() => {
    translateCardRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    pulseTranslateCard();
  }, [pulseTranslateCard]);

  const loadDailyWord = useCallback(async () => {
    const response = await fetchDailyWord();

    if (response.success && response.data) {
      setDailyWord({
        yoruba: response.data.yoruba_word,
        english: response.data.english_word
      });
    }
  }, []);

  const loadRandomProverb = useCallback(async () => {
    setProverbLoading(true);
    const response = await fetchRandomProverb();

    if (response.success && response.data) {
      setProverb({
        yoruba: response.data.yoruba_text,
        english: response.data.english_text
      });
    }

    setProverbLoading(false);
  }, []);

  const submitTranslation = useCallback(
    async (rawWord: string) => {
      const normalizedInput = rawWord.toLowerCase().trim();
      if (!normalizedInput) {
        return;
      }

      setTranslationState((previous) => ({ ...previous, loading: true }));

      const response = await translateEnglishWord(normalizedInput);

      if (response.success && response.data) {
        const translatedWord = response.data.source_word.toLowerCase();
        const targetPath = `/word/${encodeURIComponent(translatedWord)}`;

        setTranslationState({
          word: translatedWord,
          translation: response.data.translation,
          description: "",
          loading: false
        });

        if (pathname !== targetPath) {
          router.replace(targetPath, { scroll: false });
        }

        return;
      }

      const fallbackMessage = response.status === 404
        ? "We're still learning this word. Try another translation."
        : "Please check your connection and try again.";

      setTranslationState({
        word: normalizedInput,
        translation: ["(no translation found)"],
        description: response.message || fallbackMessage,
        loading: false
      });
    },
    [pathname, router]
  );

  useEffect(() => {
    void loadDailyWord();
    void loadRandomProverb();
  }, [loadDailyWord, loadRandomProverb]);

  useEffect(() => {
    if (!initialWord) {
      return;
    }

    setInput(initialWord);
    focusTranslator();
    void submitTranslation(initialWord);
  }, [focusTranslator, initialWord, submitTranslation]);

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

      <section
        ref={translateCardRef}
        className={`mt-12 rounded-3xl bg-brand-beige p-4 shadow-card transition sm:p-6 ${
          isTranslateCardHighlighted ? "ring-4 ring-brand-gold/80" : "ring-0"
        }`}
      >
        <form
          className="flex flex-col gap-3 sm:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            void submitTranslation(input);
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
            onChange={(event) => setInput(event.target.value)}
            placeholder="Enter an English word..."
            className="w-full rounded-xl border border-brand-brown/20 bg-white px-4 py-3 text-brand-ink placeholder:text-brand-ink/55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          />
          <button
            type="submit"
            className="rounded-xl bg-brand-forest px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          >
            {translationState.loading ? "Translating..." : "Translate"}
          </button>
        </form>

        <div className="mt-4 rounded-2xl bg-white p-5">
          <p className="text-xl font-semibold text-brand-ink">
            {translationState.word}
            <span className="ml-2 text-sm font-normal text-brand-ink/65">
              {translationState.word === "liaison" ? "(example)" : "(English)"}
            </span>
          </p>
          <div className="mt-2 space-y-1 text-lg italic text-brand-ink/85">
            {translationMarkup.map((line) => (
              <p key={line}>{line}</p>
            ))}
          </div>
          {translationState.description && (
            <p className="mt-3 text-sm text-brand-ink/70">{translationState.description}</p>
          )}
        </div>
      </section>

      <section className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-3">
        <article className="rounded-2xl bg-brand-beige p-4 shadow-card">
          <h2 className="font-heading text-lg text-brand-ink">Word of the Day</h2>
          <div className="mt-3 rounded-xl bg-white p-5">
            <p className="text-2xl font-semibold text-brand-ink">{dailyWord.yoruba}</p>
            {isDailyTranslationVisible && <p className="mt-2 text-lg text-brand-ink/65">{dailyWord.english}</p>}
          </div>
          <button
            type="button"
            onClick={() => setIsDailyTranslationVisible((value) => !value)}
            className="mt-3 text-sm font-semibold text-brand-forest underline decoration-brand-forest/30 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          >
            {isDailyTranslationVisible ? "Hide translation" : "View translation"}
          </button>
        </article>

        <article className="rounded-2xl bg-brand-beige p-4 shadow-card">
          <h2 className="font-heading text-lg text-brand-ink">Proverbs</h2>
          <div className="mt-3 rounded-xl bg-white p-5">
            <p className="italic text-brand-ink">{proverb.yoruba}</p>
            <p className="mt-3 text-sm text-brand-ink/70">{proverb.english}</p>
          </div>
          <button
            type="button"
            onClick={() => void loadRandomProverb()}
            disabled={proverbLoading}
            className="mt-3 text-sm font-semibold text-brand-forest underline decoration-brand-forest/30 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold disabled:opacity-60"
          >
            {proverbLoading ? "Loading..." : "Next Proverb"}
          </button>
        </article>

        <article className="rounded-2xl bg-brand-beige p-4 shadow-card">
          <h2 className="font-heading text-lg text-brand-ink">Have suggestions?</h2>
          <p className="mt-3 text-sm text-brand-ink/75">Share new words or improve existing translations.</p>
          <div className="mt-6 flex flex-col gap-3">
            <button
              type="button"
              onClick={() => setActiveModal("add-word")}
              className="rounded-xl bg-white px-4 py-3 text-sm font-semibold text-brand-ink transition hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
            >
              + Add a word
            </button>
            <button
              type="button"
              onClick={() => setActiveModal("feedback")}
              className="rounded-xl bg-white px-4 py-3 text-sm font-semibold text-brand-ink transition hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
            >
              Suggest a better translation
            </button>
          </div>
        </article>
      </section>

      {activeModal ? (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-[60] flex items-center justify-center bg-brand-ink/25 px-4 backdrop-blur-sm"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setActiveModal(null);
            }
          }}
        >
          <div className="w-full max-w-3xl overflow-hidden rounded-3xl bg-brand-beige shadow-card">
            <div className="flex items-center justify-between border-b border-brand-brown/20 px-5 py-4">
              <h3 className="font-heading text-2xl text-brand-ink">
                {activeModal === "add-word" ? "Add a New Word" : "Suggest a Better Translation"}
              </h3>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="rounded-full border border-brand-brown/25 px-3 py-1 text-sm text-brand-ink hover:bg-white"
              >
                Close
              </button>
            </div>
            <div className="h-[66vh] bg-white">
              <iframe
                title={activeModal === "add-word" ? "Add word form" : "Feedback form"}
                src={
                  activeModal === "add-word"
                    ? "https://docs.google.com/forms/d/e/1FAIpQLSe3MXuVbp-Iq9wegVzC9HRWxhA7-aBKNqgo4OZrSJ5akvEIOQ/viewform?embedded=true"
                    : "https://docs.google.com/forms/d/e/1FAIpQLScIVjG45qeyq85rZgJNldl-UDlqcMaZ2hCXt-l_mFX8ryY5VQ/viewform?embedded=true"
                }
                className="h-full w-full border-0"
              />
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
