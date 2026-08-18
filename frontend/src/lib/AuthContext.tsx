import { createContext, useContext } from "react";
import type { CurrentUser } from "./auth";

/** The server-verified user App.tsx's AuthGate fetched via GET
 * /auth/me -- lets Admin.tsx check is_admin without a second fetch. */
export const AuthContext = createContext<CurrentUser | null>(null);

export function useCurrentUser(): CurrentUser | null {
  return useContext(AuthContext);
}
