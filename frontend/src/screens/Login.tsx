import { useState } from "react";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { DhabaButton } from "../components/DhabaButton";
import { Footer } from "../components/Footer";
import { requestMagicLink } from "../lib/auth";

/** One question per screen (CLAUDE.md): just an email, then a plain-
 * language confirmation that a link is on its way. No password field
 * exists anywhere in this app -- magic-link only. */
export function Login() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSaving(true);
    setError(null);
    try {
      await requestMagicLink(email.trim());
      setSent(true);
    } catch {
      setError(t("login.error"));
    } finally {
      setSaving(false);
    }
  }

  if (sent) {
    return (
      <main className="flex min-h-dvh flex-col gap-lg p-md">
        <SignboardHeader title={t("login.check_email_title")} subtitle={t("login.check_email_subtitle", { email })} />
        <p className="text-body text-ink_body">{t("login.check_email_body")}</p>
        <DhabaButton variant="secondary" onClick={() => setSent(false)} className="w-full">
          {t("login.try_different_email")}
        </DhabaButton>
        <Footer />
      </main>
    );
  }

  return (
    <main className="flex min-h-dvh flex-col gap-lg p-md">
      <SignboardHeader title={t("login.title")} subtitle={t("login.subtitle")} />
      <div className="flex-1">
        <input
          type="email"
          inputMode="email"
          autoComplete="email"
          value={email}
          placeholder={t("login.email_placeholder")}
          onChange={(e) => setEmail(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && email.trim() && submit()}
          className="min-h-tap-primary w-full rounded-md border-2 border-tamarind_brown/30 bg-surface_card px-md text-headline text-ink_body"
          aria-label={t("login.email_placeholder")}
        />
        {error && (
          <p role="alert" className="mt-sm text-body text-accent_warning">
            {error}
          </p>
        )}
      </div>
      <DhabaButton onClick={submit} disabled={!email.trim() || saving} className="w-full">
        {saving ? t("common.loading") : t("login.send_link")}
      </DhabaButton>
      <Footer />
    </main>
  );
}
