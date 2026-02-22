import type { ProverbState } from "@/components/home/use-home-page-state";

interface ProverbCardProps {
  loading: boolean;
  onNextProverb: () => void;
  proverb: ProverbState;
}

export function ProverbCard({ loading, onNextProverb, proverb }: ProverbCardProps) {
  return (
    <article className="rounded-2xl bg-brand-beige p-4 shadow-card">
      <h2 className="font-heading text-lg text-brand-ink">Proverbs</h2>
      <div className="mt-3 rounded-xl bg-white p-5">
        <p className="italic text-brand-ink">{proverb.yoruba}</p>
        <p className="mt-3 text-sm text-brand-ink/70">{proverb.english}</p>
      </div>
      <button
        type="button"
        onClick={onNextProverb}
        disabled={loading}
        className="mt-3 text-sm font-semibold text-brand-forest underline decoration-brand-forest/30 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold disabled:opacity-60"
      >
        {loading ? "Loading..." : "Next Proverb"}
      </button>
    </article>
  );
}
