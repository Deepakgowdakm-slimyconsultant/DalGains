import type { ReactElement, ReactNode } from "react";
import { render } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter } from "react-router-dom";
import i18n from "./i18n";

// Standard wrapper for component tests: i18next (real locale strings,
// see ./i18n.ts) + a MemoryRouter (most screens use react-router hooks
// like useNavigate/useSearchParams even outside a full route tree).
function Providers({ children, route = "/" }: { children: ReactNode; route?: string }) {
  return (
    <I18nextProvider i18n={i18n}>
      <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
    </I18nextProvider>
  );
}

export function renderWithProviders(ui: ReactElement, { route = "/" }: { route?: string } = {}) {
  return render(ui, { wrapper: (props) => <Providers route={route}>{props.children}</Providers> });
}

export { default as testI18n } from "./i18n";
