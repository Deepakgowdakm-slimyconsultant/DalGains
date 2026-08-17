import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../../components/SignboardHeader";

const TABS = [
  { to: "/history/timeline", labelKey: "history.tab_timeline" },
  { to: "/history/trends", labelKey: "history.tab_trends" },
  { to: "/history/patterns", labelKey: "history.tab_patterns" },
  { to: "/history/export", labelKey: "history.tab_export" },
] as const;

/** History's own sub-nav (Timeline/Trends/Patterns/Export) -- a second
 * tab level under the bottom nav's "History" tab, not a replacement for
 * it. Each tab is a real route so state doesn't leak between them and
 * back/forward navigation works as expected. */
export function HistoryLayout() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-md p-md pb-32">
      <div className="print:hidden">
        <SignboardHeader title={t("nav.history")} />
      </div>
      <nav aria-label={t("history.tabs_label")} className="flex gap-xs overflow-x-auto print:hidden">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              "min-h-tap-min shrink-0 rounded-full border px-md py-xs text-caption font-medium " +
              (isActive ? "border-accent_action bg-accent_action text-coal_black" : "border-tamarind_brown/30 text-ink_body")
            }
          >
            {t(tab.labelKey)}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
