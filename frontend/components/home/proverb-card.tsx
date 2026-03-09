import type { ProverbState } from "@/components/home/use-home-page-state";

interface ProverbCardProps {
  loading: boolean;
  onNextProverb: () => void;
  proverb: ProverbState;
}

export function ProverbCard({ loading, onNextProverb, proverb }: ProverbCardProps) {
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-[1.25rem] border border-brand-brown/[0.06] bg-brand-cream p-6 shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card-hover">
      <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-brown/[0.06] px-3 py-1.5 text-[0.7rem] font-bold uppercase tracking-[0.15em] text-brand-brown">
        &#128214; Proverbs
      </span>
      <div className="relative mt-5 flex-1 rounded-2xl bg-white p-6 md:p-8">
        <span
          className="pointer-events-none absolute left-4 top-1 font-heading text-6xl leading-none text-brand-gold/15"
          aria-hidden="true"
        >
          &ldquo;
        </span>
        <p className="pl-6 font-heading text-lg italic leading-relaxed text-brand-ink">{proverb.yoruba}</p>
        <p className="mt-4 pl-6 text-sm text-brand-ink/50">{proverb.english}</p>
      </div>
      <button
        type="button"
        onClick={onNextProverb}
        disabled={loading}
        className="mt-4 text-sm font-semibold text-brand-forest underline decoration-brand-forest/25 underline-offset-4 transition-colors hover:text-[#227a42] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Loading..." : "Next Proverb"}
      </button>
    </article>
  );
}
