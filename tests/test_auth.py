"""Magic-link auth: request-link/verify/logout/me, plus admin-only
invitation management. Full round trip against the real backend
(TestClient), email delivery mocked (src.auth.email.send_magic_link)
so no real network call happens and the link is directly inspectable.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.auth import invitation, store
from src.auth.jwt import SESSION_COOKIE_NAME
from src.auth.magic_link import generate_link


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sent_links(monkeypatch):
    """Captures every (email, link) src.auth.email.send_magic_link would
    have sent, instead of making a real HTTP call to Resend."""
    calls = []
    monkeypatch.setattr(
        "src.api.routes.auth.send_magic_link", lambda email, link: calls.append((email, link))
    )
    return calls


def _token_from_link(link: str) -> str:
    return link.split("token=")[1]


# --- POST /auth/request-link ------------------------------------------


def test_request_link_returns_200_for_invited_email(client, sent_links):
    invitation.invite("alice@example.com", invited_by="system")
    r = client.post("/auth/request-link", json={"email": "alice@example.com"})
    assert r.status_code == 200
    assert len(sent_links) == 1
    assert sent_links[0][0] == "alice@example.com"
    # Points at this API's own /auth/verify, not a frontend URL -- that's
    # the route that actually exists and sets the cookie.
    assert "/auth/verify?token=" in sent_links[0][1]


def test_request_link_returns_200_for_uninvited_email_too(client, sent_links):
    """No account-enumeration leak: an uninvited email gets the exact
    same 200 response as an invited one."""
    r = client.post("/auth/request-link", json={"email": "stranger@example.com"})
    assert r.status_code == 200
    assert len(sent_links) == 0  # but nothing was actually sent


def test_request_link_invalid_email_returns_422(client):
    r = client.post("/auth/request-link", json={"email": "not-an-email"})
    assert r.status_code == 422


def test_request_link_works_for_existing_user_without_reinviting(client, sent_links):
    store.create_user("u1", "bob@example.com")
    r = client.post("/auth/request-link", json={"email": "bob@example.com"})
    assert r.status_code == 200
    assert len(sent_links) == 1


# --- GET /auth/verify ---------------------------------------------------


def test_verify_valid_token_creates_user_and_sets_cookie(client):
    invitation.invite("alice@example.com", invited_by="system")
    token = generate_link("alice@example.com")
    r = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    assert r.status_code == 302
    assert SESSION_COOKIE_NAME in r.cookies

    user = store.get_user_by_email("alice@example.com")
    assert user is not None
    assert user.is_admin is False


def test_verify_marks_invitation_accepted(client):
    invitation.invite("alice@example.com", invited_by="system")
    token = generate_link("alice@example.com")
    client.get(f"/auth/verify?token={token}", follow_redirects=False)
    accepted = [inv for inv in invitation.list_all() if inv.email == "alice@example.com"][0]
    assert accepted.accepted_at is not None


def test_verify_second_login_reuses_same_user_id(client):
    invitation.invite("alice@example.com", invited_by="system")
    token1 = generate_link("alice@example.com")
    client.get(f"/auth/verify?token={token1}", follow_redirects=False)
    first_id = store.get_user_by_email("alice@example.com").id

    token2 = generate_link("alice@example.com")
    client.get(f"/auth/verify?token={token2}", follow_redirects=False)
    second_id = store.get_user_by_email("alice@example.com").id
    assert first_id == second_id


def test_verify_invalid_token_returns_400(client):
    r = client.get("/auth/verify?token=not-a-real-jwt", follow_redirects=False)
    assert r.status_code == 400


def test_verify_uninvited_email_returns_403(client):
    # Token is cryptographically valid (signed correctly), but the email
    # was never invited -- a forged/leaked token for a random email must
    # not grant access.
    token = generate_link("never-invited@example.com")
    r = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    assert r.status_code == 403


def test_verify_admin_email_becomes_admin(client, monkeypatch):
    from src.config import get_settings

    invitation.invite("admin@example.com", invited_by="system")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    get_settings.cache_clear()  # get_settings() is lru_cache'd -- see src/config.py
    try:
        token = generate_link("admin@example.com")
        client.get(f"/auth/verify?token={token}", follow_redirects=False)
    finally:
        get_settings.cache_clear()

    user = store.get_user_by_email("admin@example.com")
    assert user.is_admin is True


# --- GET /auth/me / POST /auth/logout -----------------------------------


def test_me_without_cookie_returns_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_with_valid_session_returns_user(client):
    invitation.invite("alice@example.com", invited_by="system")
    token = generate_link("alice@example.com")
    verify = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    client.cookies.set(SESSION_COOKIE_NAME, verify.cookies[SESSION_COOKIE_NAME])

    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


def test_logout_clears_cookie(client):
    invitation.invite("alice@example.com", invited_by="system")
    token = generate_link("alice@example.com")
    verify = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    client.cookies.set(SESSION_COOKIE_NAME, verify.cookies[SESSION_COOKIE_NAME])

    r = client.post("/auth/logout")
    assert r.status_code == 204
    # Asserting on the Set-Cookie header directly (Max-Age=0, empty
    # value) rather than a follow-up request through the same client:
    # httpx's TestClient cookie jar doesn't reliably re-process an
    # expiring Set-Cookie the way a real browser would, so a follow-up
    # request isn't a faithful test of what the server actually told
    # the client to do.
    set_cookie = r.headers["set-cookie"]
    assert f'{SESSION_COOKIE_NAME}=""' in set_cookie
    assert "Max-Age=0" in set_cookie


# --- /admin/invitations ---------------------------------------------------


def _login_as(client: TestClient, email: str, is_admin: bool = False) -> None:
    from src.auth.jwt import create_session_token

    user = store.get_user_by_email(email)
    if user is None:
        import uuid

        user = store.create_user(str(uuid.uuid4()), email, is_admin=is_admin)
    client.cookies.set(SESSION_COOKIE_NAME, create_session_token(user.id))


def test_non_admin_cannot_create_invitation(client):
    _login_as(client, "regular@example.com", is_admin=False)
    r = client.post("/admin/invitations", json={"email": "someone@example.com"})
    assert r.status_code == 403


def test_admin_can_create_and_list_invitations(client):
    _login_as(client, "admin@example.com", is_admin=True)
    r = client.post("/admin/invitations", json={"email": "newperson@example.com"})
    assert r.status_code == 201

    r2 = client.get("/admin/invitations")
    assert r2.status_code == 200
    emails = [inv["email"] for inv in r2.json()]
    assert "newperson@example.com" in emails


def test_admin_can_revoke_invitation(client):
    _login_as(client, "admin@example.com", is_admin=True)
    client.post("/admin/invitations", json={"email": "newperson@example.com"})
    r = client.delete("/admin/invitations/newperson@example.com")
    assert r.status_code == 200
    assert r.json()["revoked_at"] is not None


def test_revoked_invitation_blocks_new_login(client, sent_links):
    invitation.invite("bad-actor@example.com", invited_by="system")
    invitation.revoke("bad-actor@example.com")

    r = client.post("/auth/request-link", json={"email": "bad-actor@example.com"})
    assert r.status_code == 200  # still no enumeration leak
    assert len(sent_links) == 0  # but no link was actually sent

    # Even a token minted before revocation must be rejected at verify.
    token = generate_link("bad-actor@example.com")
    verify = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    assert verify.status_code == 403


def test_revoke_missing_invitation_returns_404(client):
    _login_as(client, "admin@example.com", is_admin=True)
    r = client.delete("/admin/invitations/nobody@example.com")
    assert r.status_code == 404
