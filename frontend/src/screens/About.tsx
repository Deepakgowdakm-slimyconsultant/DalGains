import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { Footer } from "../components/Footer";
import { api } from "../api/client";

/** The medical disclaimer and data notice are the two things this
 * screen exists to show "without scrolling" -- kept short (matching
 * the exact wording DalGains commits to) and placed first, above
 * everything else including the footer, so a phone-sized viewport
 * shows both without the user needing to scroll past unrelated
 * content to find them. */
export function About() {
  const { t } = useTranslation();
  const [adminContact, setAdminContact] = useState<string | null>(null);

  useEffect(() => {
    api.GET("/health").then(({ data }) => data?.admin_contact && setAdminContact(data.admin_contact));
  }, []);

  return (
    <div className="flex flex-col gap-md p-md pb-32">
      <SignboardHeader title={t("about.title")} />

      <div className="rounded-md bg-surface_signboard p-md text-body text-ink_hero">
        <p className="font-semibold">{t("about.medical_disclaimer")}</p>
      </div>

      <div className="rounded-md bg-surface_primary p-md text-body text-ink_body">
        <p>{t("about.data_notice")}</p>
      </div>

      <p className="text-caption text-ink_body/70">
        {adminContact ? t("about.contact_body", { email: adminContact }) : t("about.contact_body_no_email")}
      </p>

      <Footer />
    </div>
  );
}
