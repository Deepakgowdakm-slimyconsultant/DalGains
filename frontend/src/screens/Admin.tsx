import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SignboardHeader } from "../components/SignboardHeader";
import { DhabaButton } from "../components/DhabaButton";
import { api } from "../api/client";
import type { components } from "../api/schema.gen";

type Invitation = components["schemas"]["Invitation"];

function SectionHeading({ children }: { children: string }) {
  return <h2 className="mb-sm text-headline font-display-latin text-ink_body">{children}</h2>;
}

function statusLabel(inv: Invitation, t: (key: string) => string): string {
  if (inv.revoked_at) return t("admin.status_revoked");
  if (inv.accepted_at) return t("admin.status_accepted");
  return t("admin.status_pending");
}

/** Admin-only: invite people into this invite-only app, and revoke
 * access. Only reachable if GET /auth/me's is_admin is true (see
 * App.tsx's route guard) -- the backend independently enforces the
 * same rule on every /admin/* route, so this screen isn't the only
 * thing standing between a non-admin and these actions. */
export function Admin() {
  const { t } = useTranslation();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const { data } = await api.GET("/admin/invitations");
    if (data) setInvitations(data);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function invite() {
    setSaving(true);
    setError(null);
    try {
      const { error: apiError } = await api.POST("/admin/invitations", { body: { email: email.trim() } });
      if (apiError) throw new Error();
      setEmail("");
      await refresh();
    } catch {
      setError(t("admin.invite_error"));
    } finally {
      setSaving(false);
    }
  }

  async function revoke(inviteeEmail: string) {
    await api.DELETE("/admin/invitations/{email}", { params: { path: { email: inviteeEmail } } });
    await refresh();
  }

  return (
    <div className="flex flex-col gap-lg p-md pb-32">
      <SignboardHeader title={t("admin.title")} subtitle={t("admin.subtitle")} />

      <section>
        <SectionHeading>{t("admin.invite_new")}</SectionHeading>
        <div className="flex gap-sm">
          <input
            type="email"
            inputMode="email"
            value={email}
            placeholder={t("login.email_placeholder")}
            onChange={(e) => setEmail(e.target.value)}
            className="min-h-tap-min flex-1 rounded-md border-2 border-tamarind_brown/30 bg-surface_card px-sm text-body text-ink_body"
            aria-label={t("login.email_placeholder")}
          />
          <DhabaButton onClick={invite} disabled={!email.trim() || saving}>
            {t("admin.invite_button")}
          </DhabaButton>
        </div>
        {error && (
          <p role="alert" className="mt-xs text-caption text-accent_warning">
            {error}
          </p>
        )}
      </section>

      <section>
        <SectionHeading>{t("admin.invitations_list")}</SectionHeading>
        {invitations.length === 0 ? (
          <p className="text-body text-ink_body/70">{t("admin.no_invitations")}</p>
        ) : (
          <ul className="flex flex-col gap-sm">
            {invitations.map((inv) => (
              <li key={inv.email} className="flex items-center justify-between rounded-md bg-surface_primary p-md">
                <div>
                  <p className="text-body text-ink_body">{inv.email}</p>
                  <p className="text-caption text-ink_body/70">{statusLabel(inv, t)}</p>
                </div>
                {!inv.revoked_at && (
                  <DhabaButton variant="danger" onClick={() => revoke(inv.email)}>
                    {t("admin.revoke")}
                  </DhabaButton>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
