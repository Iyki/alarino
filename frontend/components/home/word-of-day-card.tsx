import type { DailyWordState } from "@/components/home/use-home-page-state";

interface WordOfDayCardProps {
  dailyWord: DailyWordState;
  isTranslationVisible: boolean;
  onToggleTranslation: () => void;
}

export function WordOfDayCard({ dailyWord, isTranslationVisible, onToggleTranslation }: WordOfDayCardProps) {
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-[1.25rem] border border-brand-brown/[0.06] bg-brand-cream p-6 shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card-hover">
      <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-gold-light px-3 py-1.5 text-[0.7rem] font-bold uppercase tracking-[0.15em] text-brand-gold">
        &#9728; Word of the Day
      </span>
      <div className="mt-6 flex flex-1 items-center justify-center rounded-2xl bg-white p-6 text-center">
        <div>
          <p className="font-heading text-4xl font-extrabold text-brand-ink">{dailyWord.yoruba}</p>
          {isTranslationVisible ? (
            <p className="mt-2 text-lg font-medium text-brand-ink/45">{dailyWord.english}</p>
          ) : null}
        </div>
      </div>
      <button
        type="button"
        onClick={onToggleTranslation}
        className="mt-4 text-sm font-semibold text-brand-gold underline decoration-brand-gold/30 underline-offset-4 transition-colors hover:text-[#b07f1f] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
      >
        {isTranslationVisible ? "Hide translation" : "View translation"}
      </button>
    </article>
  );
}
