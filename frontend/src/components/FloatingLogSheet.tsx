import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

interface FloatingLogSheetProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

/** The bottom-sheet chrome used by the log-entry flow (search -> unit ->
 * when -> confirm). This primitive only owns the overlay/panel/close
 * button -- each step's content is supplied by the caller. */
export function FloatingLogSheet({ open, title, onClose, children }: FloatingLogSheetProps) {
  const { t } = useTranslation();
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-coal_black/40" role="presentation">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="flex max-h-[85vh] w-full max-w-app flex-col rounded-t-lg bg-surface_primary px-md pb-lg pt-sm"
      >
        <div className="mx-auto mb-sm h-1.5 w-12 rounded-full bg-tamarind_brown/30" aria-hidden="true" />
        <div className="flex items-center justify-between pb-sm">
          <h2 className="text-headline font-display-latin text-ink_body">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("common.cancel")}
            className="flex min-h-tap-min min-w-tap-min items-center justify-center rounded-full text-headline text-ink_body"
          >
            &times;
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
