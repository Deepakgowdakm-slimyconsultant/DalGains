import { Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { Onboarding } from "./screens/Onboarding";
import { Home } from "./screens/Home";
import { Weekly } from "./screens/Weekly";
import { Insights } from "./screens/Insights";
import { Profile } from "./screens/Profile";
import { getCurrentUserId } from "./lib/currentUser";

// Temporary placeholder for routes not yet built in Part C -- replaced
// screen by screen across the remaining Part C commits.
function ComingSoon({ label }: { label: string }) {
  return <div className="p-md text-body text-ink_body">{label} -- coming soon.</div>;
}

function RequireProfile({ children }: { children: React.ReactNode }) {
  if (!getCurrentUserId()) return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <Suspense fallback={null}>
      <BrowserRouter>
        <Routes>
          <Route path="/onboarding" element={<Onboarding />} />
          <Route
            element={
              <RequireProfile>
                <AppShell />
              </RequireProfile>
            }
          >
            <Route path="/" element={<Home />} />
            <Route path="/weekly" element={<Weekly />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/history/*" element={<ComingSoon label="History" />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Suspense>
  );
}

export default App;
