import { useTranslation } from "react-i18next";

const REPO_URL = "https://github.com/Deepakgowdakm-slimyconsultant/DalGains";

/** Present on every screen (AGPL-3.0 obligation, not optional -- see
 * LICENSE). Placed at the end of each screen's scrollable content
 * rather than pinned, so it doesn't compete with the fixed bottom nav
 * for space; "present on every screen" doesn't require "always visible
 * without scrolling" the way the About screen's medical disclaimer
 * does. */
export function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="p-md text-center text-caption text-ink_body/60">
      <p>
        {t("footer.agpl_notice")}{" "}
        <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="underline">
          {t("footer.view_source")}
        </a>
      </p>
    </footer>
  );
}
