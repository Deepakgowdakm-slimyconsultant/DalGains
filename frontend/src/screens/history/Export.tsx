import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { DhabaButton } from "../../components/DhabaButton";
import { getCurrentUserId } from "../../lib/currentUser";
import { useHistoryData } from "./useHistoryData";
import { EmptyHistoryState } from "./EmptyHistoryState";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function daysAgoIso(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

function downloadBlob(content: string, mimeType: string, filename: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function SectionHeading({ children }: { children: string }) {
  return <h2 className="mb-sm text-headline font-display-latin text-ink_body">{children}</h2>;
}

export function Export() {
  const { t } = useTranslation();
  const userId = getCurrentUserId()!;
  const { profile, plan, logs, loading } = useHistoryData(userId);
  const [startDate, setStartDate] = useState(daysAgoIso(29));
  const [endDate, setEndDate] = useState(todayIso());

  const inRange = useMemo(
    () => logs.filter((l) => l.log_id >= startDate && l.log_id <= endDate).sort((a, b) => a.log_id.localeCompare(b.log_id)),
    [logs, startDate, endDate]
  );

  function exportJson() {
    const payload = {
      user: profile?.name ?? userId,
      range: { start: startDate, end: endDate },
      plan,
      days: inRange.map((l) => ({ date: l.log_id, totals: l.computed_totals, entry_count: l.entries.length })),
    };
    downloadBlob(JSON.stringify(payload, null, 2), "application/json", `dalgains-${startDate}-to-${endDate}.json`);
  }

  function exportCsv() {
    const header = "date,energy_kcal,protein_g,fat_g,carbs_g,fiber_g,entry_count";
    const rows = inRange.map((l) => {
      const t = l.computed_totals;
      return [l.log_id, t.energy_kcal.toFixed(1), t.protein_g.toFixed(1), t.fat_g.toFixed(1), t.carbs_g.toFixed(1), t.fiber_g.toFixed(1), l.entries.length].join(",");
    });
    downloadBlob([header, ...rows].join("\n"), "text/csv", `dalgains-${startDate}-to-${endDate}.csv`);
  }

  function printSummary() {
    // A dedicated print stylesheet turns this same page into a clean
    // printable summary via the browser's native print-to-PDF -- avoids
    // pulling in a PDF-generation library for one screen.
    window.print();
  }

  function shareWithDietitian() {
    const avg =
      inRange.length > 0
        ? inRange.reduce(
            (sum, l) => ({
              energy_kcal: sum.energy_kcal + l.computed_totals.energy_kcal / inRange.length,
              protein_g: sum.protein_g + l.computed_totals.protein_g / inRange.length,
              fat_g: sum.fat_g + l.computed_totals.fat_g / inRange.length,
              carbs_g: sum.carbs_g + l.computed_totals.carbs_g / inRange.length,
              fiber_g: sum.fiber_g + l.computed_totals.fiber_g / inRange.length,
            }),
            { energy_kcal: 0, protein_g: 0, fat_g: 0, carbs_g: 0, fiber_g: 0 }
          )
        : null;
    const lines = [
      `DalGains summary for ${profile?.name ?? userId}`,
      `Range: ${startDate} to ${endDate} (${inRange.length} logged days)`,
      plan ? `Daily target: ${Math.round(plan.daily_kcal)} kcal, ${Math.round(plan.protein_g)}g protein` : "",
      avg
        ? `Averages: ${Math.round(avg.energy_kcal)} kcal, ${Math.round(avg.protein_g)}g protein, ${Math.round(avg.fat_g)}g fat, ${Math.round(avg.carbs_g)}g carbs, ${Math.round(avg.fiber_g)}g fiber`
        : "No days logged in this range",
      "",
      "This is a summary only -- not raw daily logs.",
    ];
    // No server-side sharing yet (Phase 5) -- a downloadable summary
    // file is the "local file for now" the brief asks for, something a
    // user can attach to an email or message themselves.
    downloadBlob(lines.filter(Boolean).join("\n"), "text/plain", `dalgains-summary-${startDate}-to-${endDate}.txt`);
  }

  if (loading) return <p className="text-body text-ink_body">{t("weekly.loading")}</p>;
  if (logs.length === 0) return <EmptyHistoryState />;

  return (
    <div className="flex flex-col gap-lg print:p-lg">
      <section className="print:hidden">
        <SectionHeading>{t("history.export_range")}</SectionHeading>
        <div className="flex items-center gap-sm rounded-md bg-surface_primary p-md">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="min-h-tap-min flex-1 rounded-md border-2 border-tamarind_brown/30 bg-surface_card px-sm text-body text-ink_body"
          />
          <span className="text-body text-ink_body">{t("history.export_to")}</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="min-h-tap-min flex-1 rounded-md border-2 border-tamarind_brown/30 bg-surface_card px-sm text-body text-ink_body"
          />
        </div>
        <p className="mt-xs text-caption text-ink_body/70">{t("history.export_day_count", { count: inRange.length })}</p>
      </section>

      <section className="print:hidden">
        <SectionHeading>{t("history.export_title")}</SectionHeading>
        <div className="flex flex-col gap-sm">
          <DhabaButton variant="secondary" onClick={exportJson} className="w-full">
            {t("history.export_json")}
          </DhabaButton>
          <DhabaButton variant="secondary" onClick={exportCsv} className="w-full">
            {t("history.export_csv")}
          </DhabaButton>
          <DhabaButton variant="secondary" onClick={printSummary} className="w-full">
            {t("history.export_pdf")}
          </DhabaButton>
        </div>
      </section>

      <section className="print:hidden">
        <SectionHeading>{t("history.share_title")}</SectionHeading>
        <p className="mb-sm text-caption text-ink_body/70">{t("history.share_note")}</p>
        <DhabaButton onClick={shareWithDietitian} className="w-full">
          {t("history.share_button")}
        </DhabaButton>
      </section>

      {/* Print-only summary view -- shown via @media print, hidden on screen. */}
      <section className="hidden print:block">
        <h1 className="font-display-latin text-display text-ink_body">DalGains -- {profile?.name}</h1>
        <p className="text-body text-ink_body">{startDate} - {endDate}</p>
        <table className="mt-md w-full border-collapse text-body text-ink_body">
          <thead>
            <tr>
              <th className="border border-tamarind_brown/30 p-xs text-left">{t("history.export_date_column")}</th>
              <th className="border border-tamarind_brown/30 p-xs text-left">{t("logging.preview_kcal")}</th>
              <th className="border border-tamarind_brown/30 p-xs text-left">{t("logging.preview_protein")}</th>
              <th className="border border-tamarind_brown/30 p-xs text-left">{t("logging.preview_fat")}</th>
              <th className="border border-tamarind_brown/30 p-xs text-left">{t("logging.preview_carbs")}</th>
            </tr>
          </thead>
          <tbody>
            {inRange.map((l) => (
              <tr key={l.log_id}>
                <td className="border border-tamarind_brown/30 p-xs">{l.log_id}</td>
                <td className="border border-tamarind_brown/30 p-xs">{Math.round(l.computed_totals.energy_kcal)}</td>
                <td className="border border-tamarind_brown/30 p-xs">{Math.round(l.computed_totals.protein_g)}</td>
                <td className="border border-tamarind_brown/30 p-xs">{Math.round(l.computed_totals.fat_g)}</td>
                <td className="border border-tamarind_brown/30 p-xs">{Math.round(l.computed_totals.carbs_g)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
