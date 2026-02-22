import type { ProverbState } from "@/components/home/use-home-page-state";

interface ProverbCardProps {
  loading: boolean;
  onNextProverb: () => void;
  proverb: ProverbState;
}

export function ProverbCard({ loading, onNextProverb, proverb }: ProverbCardProps) {
  return (
    <article className="rounded-2xl bg-brand-cream p-5 shadow-card transition-all duration-200 hover:shadow-card-hover">
      <div className="flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-terracotta/10 text-brand-terracotta">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
          </svg>
        </span>
        <h2 className="font-heading text-lg font-semibold text-brand-ink">Proverbs</h2>
      </div>
      <div className="mt-4 rounded-xl bg-white p-5 shadow-sm">
        <p className="font-heading italic leading-relaxed text-brand-ink">{proverb.yoruba}</p>
        <p className="mt-3 text-sm text-brand-ink/65">{proverb.english}</p>
      </div>
      <button
        type="button"
        onClick={onNextProverb}
        disabled={loading}
        className="mt-4 text-sm font-semibold text-brand-terracotta underline decoration-brand-terracotta/30 underline-offset-4 transition-colors hover:text-brand-terracotta/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Loading..." : "Next Proverb"}
      </button>
    </article>
  );
}
