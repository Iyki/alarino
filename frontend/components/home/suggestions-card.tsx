import type { ModalType } from "@/components/home/use-home-page-state";

interface SuggestionsCardProps {
  onOpenModal: (modal: Exclude<ModalType, null>) => void;
}

export function SuggestionsCard({ onOpenModal }: SuggestionsCardProps) {
  return (
    <article className="flex h-full flex-col rounded-2xl bg-brand-cream p-5 shadow-card transition-all duration-200 hover:shadow-card-hover">
      <div className="flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-indigo/10 text-brand-indigo">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 011.037-.443 48.282 48.282 0 005.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
          </svg>
        </span>
        <h2 className="font-heading text-lg font-semibold text-brand-ink">Have suggestions?</h2>
      </div>
      <p className="mt-3 text-sm text-brand-ink/65">Share new words or improve existing translations.</p>
      <div className="mt-5 flex flex-1 flex-col gap-3">
        <button
          type="button"
          onClick={() => onOpenModal("add-word")}
          className="rounded-xl border border-brand-indigo/15 bg-white px-4 py-3 text-sm font-semibold text-brand-ink shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-indigo/30 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          + Add a word
        </button>
        <button
          type="button"
          onClick={() => onOpenModal("feedback")}
          className="rounded-xl border border-brand-indigo/15 bg-white px-4 py-3 text-sm font-semibold text-brand-ink shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-indigo/30 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          Suggest a better translation
        </button>
      </div>
    </article>
  );
}
