import type { DailyWordState } from "@/components/home/use-home-page-state";

interface WordOfDayCardProps {
  dailyWord: DailyWordState;
  isTranslationVisible: boolean;
  onToggleTranslation: () => void;
}

export function WordOfDayCard({ dailyWord, isTranslationVisible, onToggleTranslation }: WordOfDayCardProps) {
  return (
    <article className="rounded-2xl bg-brand-beige p-4 shadow-card">
      <h2 className="font-heading text-lg text-brand-ink">Word of the Day</h2>
      <div className="mt-3 rounded-xl bg-white p-5">
        <p className="text-2xl font-semibold text-brand-ink">{dailyWord.yoruba}</p>
        {isTranslationVisible ? <p className="mt-2 text-lg text-brand-ink/65">{dailyWord.english}</p> : null}
      </div>
      <button
        type="button"
        onClick={onToggleTranslation}
        className="mt-3 text-sm font-semibold text-brand-forest underline decoration-brand-forest/30 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
      >
        {isTranslationVisible ? "Hide translation" : "View translation"}
      </button>
    </article>
  );
}
