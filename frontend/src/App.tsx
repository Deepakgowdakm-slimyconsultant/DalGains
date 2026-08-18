import { Suspense, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { Login } from "./screens/Login";
import { Onboarding } from "./screens/Onboarding";
import { Admin } from "./screens/Admin";
import { Home } from "./screens/Home";
import { Weekly } from "./screens/Weekly";
import { Insights } from "./screens/Insights";
import { Profile } from "./screens/Profile";
import { HistoryLayout } from "./screens/history/HistoryLayout";
import { Timeline } from "./screens/history/Timeline";
import { Trends } from "./screens/history/Trends";
import { Patterns } from "./screens/history/Patterns";
import { Export } from "./screens/history/Export";
import { api } from "./api/client";
import { fetchCurrentUser } from "./lib/auth";
import type { CurrentUser } from "./lib/auth";
import { AuthContext, useCurrentUser } from "./lib/AuthContext";
import { clearCurrentUserId, getCurrentUserId, setCurrentUserId } from "./lib/currentUser";

/** Checks the real session (GET /auth/me), not just "is there something
 * in localStorage" -- that used to be the whole check (Phase 4, no
 * auth), but a client-set value proves nothing about who's actually
 * logged in server-side. Populates the local cache other screens read
 * via getCurrentUserId() once the server confirms who's logged in, and
 * provides the fetched user via AuthContext so nested guards (Admin)
 * don't need a second round trip. */
function AuthGate({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<"loading" | "authed" | "anon">("loading");
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    fetchCurrentUser().then((fetched) => {
      if (fetched) {
        setCurrentUserId(fetched.id);
        setUser(fetched);
        setStatus("authed");
      } else {
        clearCurrentUserId();
        setStatus("anon");
      }
    });
  }, []);

  if (status === "loading") return null;
  if (status === "anon") return <Navigate to="/login" replace />;
  return <AuthContext.Provider value={user}>{children}</AuthContext.Provider>;
}

/** Distinct from AuthGate: being logged in isn't the same as having
 * finished onboarding (a first-time user has neither yet). */
function RequireProfile({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<"loading" | "has_profile" | "no_profile">("loading");

  useEffect(() => {
    const userId = getCurrentUserId();
    if (!userId) {
      setStatus("no_profile");
      return;
    }
    api.GET("/profile/{user_id}", { params: { path: { user_id: userId } } }).then(({ response }) => {
      setStatus(response.status === 200 ? "has_profile" : "no_profile");
    });
  }, []);

  if (status === "loading") return null;
  if (status === "no_profile") return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
}

function AdminGate({ children }: { children: React.ReactNode }) {
  const user = useCurrentUser();
  if (!user?.is_admin) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <Suspense fallback={null}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/onboarding"
            element={
              <AuthGate>
                <Onboarding />
              </AuthGate>
            }
          />
          <Route
            element={
              <AuthGate>
                <RequireProfile>
                  <AppShell />
                </RequireProfile>
              </AuthGate>
            }
          >
            <Route path="/" element={<Home />} />
            <Route path="/weekly" element={<Weekly />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/history" element={<HistoryLayout />}>
              <Route index element={<Navigate to="/history/timeline" replace />} />
              <Route path="timeline" element={<Timeline />} />
              <Route path="trends" element={<Trends />} />
              <Route path="patterns" element={<Patterns />} />
              <Route path="export" element={<Export />} />
            </Route>
            <Route path="/profile" element={<Profile />} />
            <Route
              path="/admin"
              element={
                <AdminGate>
                  <Admin />
                </AdminGate>
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </Suspense>
  );
}

export default App;
