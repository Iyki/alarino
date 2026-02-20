import type { ModalType } from "@/components/home/use-home-page-state";

interface SuggestionsCardProps {
  onOpenModal: (modal: Exclude<ModalType, null>) => void;
}

export function SuggestionsCard({ onOpenModal }: SuggestionsCardProps) {
  return (
    <article className="rounded-2xl bg-brand-beige p-4 shadow-card">
      <h2 className="font-heading text-lg text-brand-ink">Have suggestions?</h2>
      <p className="mt-3 text-sm text-brand-ink/75">Share new words or improve existing translations.</p>
      <div className="mt-6 flex flex-col gap-3">
        <button
          type="button"
          onClick={() => onOpenModal("add-word")}
          className="rounded-xl bg-white px-4 py-3 text-sm font-semibold text-brand-ink transition hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          + Add a word
        </button>
        <button
          type="button"
          onClick={() => onOpenModal("feedback")}
          className="rounded-xl bg-white px-4 py-3 text-sm font-semibold text-brand-ink transition hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          Suggest a better translation
        </button>
      </div>
    </article>
  );
}
