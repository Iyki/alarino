import type { DailyWordState } from "@/components/home/use-home-page-state";

interface WordOfDayCardProps {
  dailyWord: DailyWordState;
  isTranslationVisible: boolean;
  onToggleTranslation: () => void;
}

export function WordOfDayCard({ dailyWord, isTranslationVisible, onToggleTranslation }: WordOfDayCardProps) {
  return (
    <article className="rounded-2xl bg-brand-cream p-5 shadow-card transition-all duration-200 hover:shadow-card-hover">
      <div className="flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gold-light text-brand-gold">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
          </svg>
        </span>
        <h2 className="font-heading text-lg font-semibold text-brand-ink">Word of the Day</h2>
      </div>
      <div className="mt-4 rounded-xl bg-white p-5 shadow-sm">
        <p className="font-heading text-2xl font-bold text-brand-ink">{dailyWord.yoruba}</p>
        {isTranslationVisible ? <p className="mt-2 text-lg text-brand-ink/60">{dailyWord.english}</p> : null}
      </div>
      <button
        type="button"
        onClick={onToggleTranslation}
        className="mt-4 text-sm font-semibold text-brand-gold underline decoration-brand-gold/30 underline-offset-4 transition-colors hover:text-brand-gold/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
      >
        {isTranslationVisible ? "Hide translation" : "View translation"}
      </button>
    </article>
  );
}
