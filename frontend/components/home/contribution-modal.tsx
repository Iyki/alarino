import { ADD_WORD_FORM_URL, FEEDBACK_FORM_URL } from "@/lib/constants";
import type { ModalType } from "@/components/home/use-home-page-state";

interface ContributionModalProps {
  activeModal: Exclude<ModalType, null> | null;
  onClose: () => void;
}

export function ContributionModal({ activeModal, onClose }: ContributionModalProps) {
  if (!activeModal) {
    return null;
  }

  const isAddWordModal = activeModal === "add-word";
  const title = isAddWordModal ? "Add a New Word" : "Suggest a Better Translation";
  const iframeTitle = isAddWordModal ? "Add word form" : "Feedback form";
  const iframeSrc = isAddWordModal ? ADD_WORD_FORM_URL : FEEDBACK_FORM_URL;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-[60] flex items-center justify-center bg-brand-ink/40 px-4 backdrop-blur-sm"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="w-full max-w-3xl overflow-hidden rounded-3xl bg-brand-cream shadow-2xl">
        <div className="flex items-center justify-between border-b border-brand-brown/10 px-6 py-4">
          <h3 className="font-heading text-xl font-semibold text-brand-ink">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-brand-brown/15 bg-white px-3 py-1.5 text-sm font-medium text-brand-ink transition-colors hover:bg-brand-beige focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          >
            Close
          </button>
        </div>
        <div className="h-[66vh] bg-white">
          <iframe title={iframeTitle} src={iframeSrc} className="h-full w-full border-0" />
        </div>
      </div>
    </div>
  );
}
