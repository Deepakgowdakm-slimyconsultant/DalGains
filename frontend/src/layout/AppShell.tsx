import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

interface NavItem {
  to: string;
  labelKey: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", labelKey: "nav.today", icon: "\u{1F3E0}" },
  { to: "/weekly", labelKey: "nav.week", icon: "\u{1F4C5}" },
  { to: "/insights", labelKey: "nav.insights", icon: "\u{1F4A1}" },
  { to: "/history", labelKey: "nav.history", icon: "\u{1F4DC}" },
  { to: "/profile", labelKey: "nav.profile", icon: "\u{1F464}" },
];

/** Mobile-first single-column app shell, max-width 480px centered on
 * desktop, with a bottom nav bar. Every nav item carries a text label
 * under its icon -- never icon-only, per CLAUDE.md's elderly-usability
 * rule. */
export function AppShell() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-dvh flex-col bg-surface_primary dark:bg-dark-surface_primary">
      <div className="flex-1 overflow-y-auto pb-24">
        <Outlet />
      </div>
      <nav
        aria-label={t("nav.label")}
        className="fixed inset-x-0 bottom-0 mx-auto flex w-full max-w-app justify-around border-t border-tamarind_brown/15 bg-signboard_white pb-[env(safe-area-inset-bottom)] dark:bg-dark-surface_primary"
      >
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              "flex min-h-tap-primary flex-1 flex-col items-center justify-center gap-0.5 text-caption " +
              (isActive ? "text-accent_action font-semibold" : "text-ink_body/70")
            }
          >
            <span aria-hidden="true" className="text-headline leading-none">
              {item.icon}
            </span>
            <span>{t(item.labelKey)}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
