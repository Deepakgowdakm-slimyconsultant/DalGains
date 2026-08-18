import { useTranslation } from "react-i18next";

/** New-user case for every History tab: "keep logging, insights unlock
 * at 7/14/30 days" rather than a blank chart or empty list. */
export function EmptyHistoryState() {
  const { t } = useTranslation();
  return (
    <div className="rounded-md bg-surface_primary p-lg text-center">
      <p className="text-body text-ink_body">{t("history.empty_state")}</p>
    </div>
  );
}
