"use client";

import { useCallback, useEffect, useState } from "react";

import { DEFAULT_TRANSLATION_LINES, DEFAULT_TRANSLATION_WORD } from "@/lib/constants";
import { fetchDailyWord, fetchRandomProverb, translateEnglishWord } from "@/lib/api";

export type ModalType = "add-word" | "feedback" | null;

export type TranslationViewState = {
  word: string;
  translation: string[];
  description: string;
  loading: boolean;
};

export type DailyWordState = {
  yoruba: string;
  english: string;
};

export type ProverbState = {
  yoruba: string;
  english: string;
};

const EMPTY_TRANSLATION_STATE: TranslationViewState = {
  word: DEFAULT_TRANSLATION_WORD,
  translation: DEFAULT_TRANSLATION_LINES,
  description: "",
  loading: false
};

const INITIAL_DAILY_WORD: DailyWordState = {
  yoruba: "ìfẹ́",
  english: "love"
};

const INITIAL_PROVERB: ProverbState = {
  yoruba: "Bí ojú kò bá rí, ẹnu kì í sọ nǹkan.",
  english: "If the eye does not see, the mouth says nothing."
};

interface UseHomePageStateOptions {
  initialWord?: string;
  onTranslatedWord?: (word: string) => void;
}

export function useHomePageState({ initialWord, onTranslatedWord }: UseHomePageStateOptions) {
  const [input, setInput] = useState(initialWord ?? "");
  const [translationState, setTranslationState] = useState<TranslationViewState>(EMPTY_TRANSLATION_STATE);
  const [dailyWord, setDailyWord] = useState<DailyWordState>(INITIAL_DAILY_WORD);
  const [isDailyTranslationVisible, setIsDailyTranslationVisible] = useState(false);
  const [proverb, setProverb] = useState<ProverbState>(INITIAL_PROVERB);
  const [proverbLoading, setProverbLoading] = useState(false);
  const [activeModal, setActiveModal] = useState<ModalType>(null);

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

        setTranslationState({
          word: translatedWord,
          translation: response.data.translation,
          description: "",
          loading: false
        });

        onTranslatedWord?.(translatedWord);
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
    [onTranslatedWord]
  );

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

  const toggleDailyTranslation = useCallback(() => {
    setIsDailyTranslationVisible((value) => !value);
  }, []);

  useEffect(() => {
    void loadDailyWord();
    void loadRandomProverb();
  }, [loadDailyWord, loadRandomProverb]);

  useEffect(() => {
    if (!initialWord) {
      return;
    }

    setInput(initialWord);
    void submitTranslation(initialWord);
  }, [initialWord, submitTranslation]);

  return {
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
  };
}
