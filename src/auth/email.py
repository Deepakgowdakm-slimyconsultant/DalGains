"""Magic-link delivery via Resend (resend.com) -- free tier, no credit
card, 100 emails/day / 3,000/month, comfortably covers an invite-only
household-scale app. Falls back to logging the link to stdout when
RESEND_API_KEY isn't set, which is every local-dev run by default --
nobody needs a real Resend account just to run the app on their laptop.
"""
import logging

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
# Resend's sandbox "from" address -- works with any Resend account with
# zero domain-verification setup, fine for an invite-only app where the
# recipient list is small and known. Swap for a verified custom domain
# address once DalGains has one (see scripts/deploy_hf_spaces.md).
FROM_ADDRESS = "DalGains <onboarding@resend.dev>"


def send_magic_link(email: str, link: str) -> None:
    api_key = get_settings().RESEND_API_KEY
    if not api_key:
        logger.info("RESEND_API_KEY not set -- logging magic link instead of emailing it.")
        print(f"\n[dev-only] Magic link for {email}:\n  {link}\n")
        return

    response = httpx.post(
        RESEND_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": FROM_ADDRESS,
            "to": [email],
            "subject": "Your DalGains sign-in link",
            "html": (
                f"<p>Tap the link below to sign in to DalGains. It expires in 24 hours.</p>"
                f'<p><a href="{link}">{link}</a></p>'
                f"<p>Didn't request this? You can ignore this email.</p>"
            ),
        },
        timeout=10,
    )
    response.raise_for_status()
