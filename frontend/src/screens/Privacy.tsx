import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { Footer } from "../components/Footer";
import { api } from "../api/client";

/** Public (no login required) -- same reasoning as Terms.tsx. Covers
 * what DPDP Act 2023 (India's data protection law) requires a data
 * fiduciary to tell users: what's collected, why, where it's stored,
 * and how to exercise access/correction/deletion rights. */
export function Privacy() {
  const { t } = useTranslation();
  const [adminContact, setAdminContact] = useState<string | null>(null);

  useEffect(() => {
    api.GET("/health").then(({ data }) => data?.admin_contact && setAdminContact(data.admin_contact));
  }, []);

  return (
    <main className="mx-auto flex min-h-dvh max-w-app flex-col gap-md p-md">
      <SignboardHeader title={t("privacy.title")} />
      <div className="flex flex-col gap-md text-body text-ink_body">
        <p>{t("privacy.intro")}</p>

        <h2 className="text-headline font-display-latin">{t("privacy.what_we_collect_title")}</h2>
        <p>{t("privacy.what_we_collect_body")}</p>

        <h2 className="text-headline font-display-latin">{t("privacy.where_stored_title")}</h2>
        <p>{t("privacy.where_stored_body")}</p>

        <h2 className="text-headline font-display-latin">{t("privacy.your_rights_title")}</h2>
        <p>{t("privacy.your_rights_body")}</p>

        <h2 className="text-headline font-display-latin">{t("privacy.dpdp_title")}</h2>
        <p>{t("privacy.dpdp_body")}</p>

        <h2 className="text-headline font-display-latin">{t("privacy.contact_title")}</h2>
        <p>{adminContact ? t("privacy.contact_body", { email: adminContact }) : t("privacy.contact_body_no_email")}</p>
      </div>
      <Footer />
    </main>
  );
}
