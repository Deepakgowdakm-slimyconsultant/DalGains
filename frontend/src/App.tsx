import { Suspense } from "react";
import { useTranslation } from "react-i18next";

function Scaffold() {
  const { t } = useTranslation();
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6">
      <h1 className="font-display-latin text-hero text-ink_body">DalGains</h1>
      <p className="text-body text-ink_body">{t("logging.how_much_roughly")}</p>
    </main>
  );
}

function App() {
  return (
    <Suspense fallback={null}>
      <Scaffold />
    </Suspense>
  );
}

export default App;
