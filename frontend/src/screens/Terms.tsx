import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { Footer } from "../components/Footer";

/** Public (no login required) -- linked from Onboarding's consent step
 * and reachable directly, since a plain-language legal page shouldn't
 * require an account to read. Written as a real screen (translated via
 * i18n like everything else in this app) rather than a rendered .md
 * file + parser dependency -- "markdown pages" here means the writing
 * style (short paragraphs, plain headings), not a literal file format. */
export function Terms() {
  const { t } = useTranslation();
  return (
    <main className="mx-auto flex min-h-dvh max-w-app flex-col gap-md p-md">
      <SignboardHeader title={t("terms.title")} />
      <div className="flex flex-col gap-md text-body text-ink_body">
        <p>{t("terms.intro")}</p>
        <h2 className="text-headline font-display-latin">{t("terms.section_use_title")}</h2>
        <p>{t("terms.section_use_body")}</p>
        <h2 className="text-headline font-display-latin">{t("terms.section_no_warranty_title")}</h2>
        <p>{t("terms.section_no_warranty_body")}</p>
        <h2 className="text-headline font-display-latin">{t("terms.section_open_source_title")}</h2>
        <p>{t("terms.section_open_source_body")}</p>
      </div>
      <Footer />
    </main>
  );
}
