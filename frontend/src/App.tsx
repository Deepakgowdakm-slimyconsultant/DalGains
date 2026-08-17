import { Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { Onboarding } from "./screens/Onboarding";
import { Home } from "./screens/Home";
import { Weekly } from "./screens/Weekly";
import { Insights } from "./screens/Insights";
import { Profile } from "./screens/Profile";
import { HistoryLayout } from "./screens/history/HistoryLayout";
import { Timeline } from "./screens/history/Timeline";
import { Trends } from "./screens/history/Trends";
import { ComingSoonTab } from "./screens/history/ComingSoonTab";
import { getCurrentUserId } from "./lib/currentUser";

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
            <Route path="/history" element={<HistoryLayout />}>
              <Route index element={<Navigate to="/history/timeline" replace />} />
              <Route path="timeline" element={<Timeline />} />
              <Route path="trends" element={<Trends />} />
              {/* Patterns/Export land in the next two Part D commits. */}
              <Route path="patterns" element={<ComingSoonTab label="Patterns" />} />
              <Route path="export" element={<ComingSoonTab label="Export" />} />
            </Route>
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Suspense>
  );
}

export default App;
