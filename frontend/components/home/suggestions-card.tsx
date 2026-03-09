import type { ModalType } from "@/components/home/use-home-page-state";

interface SuggestionsCardProps {
  onOpenModal: (modal: Exclude<ModalType, null>) => void;
}

export function SuggestionsCard({ onOpenModal }: SuggestionsCardProps) {
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-[1.25rem] border border-brand-brown/[0.06] bg-brand-cream p-6 shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card-hover">
      <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-brown/[0.06] px-3 py-1.5 text-[0.7rem] font-bold uppercase tracking-[0.15em] text-brand-brown">
        &#128172; Community
      </span>
      <h3 className="mt-5 font-heading text-xl font-bold text-brand-ink">Have suggestions?</h3>
      <p className="mt-2 text-sm text-brand-ink/50">Share new words or improve existing translations.</p>
      <div className="mt-5 flex flex-1 flex-col gap-2.5">
        <button
          type="button"
          onClick={() => onOpenModal("add-word")}
          className="flex items-center rounded-[0.875rem] border-[1.5px] border-brand-brown/[0.08] bg-white px-4 py-3.5 text-left text-sm font-semibold text-brand-ink transition-all duration-200 hover:-translate-y-px hover:border-brand-forest/20 hover:bg-brand-forest-light hover:shadow-[0_2px_8px_rgba(26,18,7,0.06)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-brand-forest-light text-sm text-brand-forest">
            +
          </span>
          Add a word
        </button>
        <button
          type="button"
          onClick={() => onOpenModal("feedback")}
          className="flex items-center rounded-[0.875rem] border-[1.5px] border-brand-brown/[0.08] bg-white px-4 py-3.5 text-left text-sm font-semibold text-brand-ink transition-all duration-200 hover:-translate-y-px hover:border-brand-forest/20 hover:bg-brand-forest-light hover:shadow-[0_2px_8px_rgba(26,18,7,0.06)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-brand-forest-light text-sm text-brand-forest">
            &#9998;
          </span>
          Suggest a better translation
        </button>
      </div>
    </article>
  );
}
