import { Suspense, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AppShell } from "./layout/AppShell";
import { SignboardHeader } from "./components/SignboardHeader";
import { KatoriProgressRing } from "./components/KatoriProgressRing";
import { ThaliCard } from "./components/ThaliCard";
import { DhabaButton } from "./components/DhabaButton";
import { SpiceChip } from "./components/SpiceChip";
import { FloatingLogSheet } from "./components/FloatingLogSheet";

// Temporary placeholder route content -- Part C replaces every one of
// these with a real screen (src/screens/*). This exists only to prove
// the six component primitives and the AppShell layout render correctly
// together before screen work starts.
function PrimitivesPreview() {
  const { t } = useTranslation();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [filter, setFilter] = useState("high_protein");

  return (
    <div className="flex flex-col gap-lg p-md">
      <SignboardHeader title="DalGains" subtitle="Component primitives preview" />

      <div className="flex justify-center gap-md">
        <KatoriProgressRing label="kcal" current={1450} target={2000} size="primary" />
        <div className="flex gap-sm">
          <KatoriProgressRing label="Protein" current={80} target={110} colorToken="accent_success" />
          <KatoriProgressRing label="Fat" current={40} target={60} colorToken="accent_celebration" />
          <KatoriProgressRing label="Carbs" current={180} target={220} colorToken="accent_action" />
        </div>
      </div>

      <ThaliCard title="Toor dal, 1 katori" subtitle="Lunch" meta="180 kcal" icon={<span>🥣</span>} />

      <div className="flex gap-sm">
        {["high_protein", "over_target", "on_target"].map((key) => (
          <SpiceChip key={key} label={key} selected={filter === key} onClick={() => setFilter(key)} />
        ))}
      </div>

      <DhabaButton onClick={() => setSheetOpen(true)}>{t("common.log_this")}</DhabaButton>

      <FloatingLogSheet open={sheetOpen} title={t("logging.how_much_roughly")} onClose={() => setSheetOpen(false)}>
        <p className="p-md text-body text-ink_body">Sheet content goes here (Part C, log-entry flow).</p>
      </FloatingLogSheet>
    </div>
  );
}

function App() {
  return (
    <Suspense fallback={null}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<PrimitivesPreview />} />
            <Route path="/weekly" element={<PrimitivesPreview />} />
            <Route path="/insights" element={<PrimitivesPreview />} />
            <Route path="/history" element={<PrimitivesPreview />} />
            <Route path="/profile" element={<PrimitivesPreview />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Suspense>
  );
}

export default App;
