"""FND-05: argon2 passwords, expiring JWTs, role guards on every router.

What these pin: no route outside register/login answers without a token; each
router refuses the roles it is not for; an applicant reads only their own
record; expired, forged and orphaned tokens are rejected; the demo account
exists and works only under DEMO_MODE; the app will not start without a
usable AUTH_SECRET. Everything runs offline: no route here reaches a model.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend import settings
from backend.db import feynman as feynman_store
from backend.db import users as user_store
from backend.db.candidates import applicant_id_for
from backend.db.seed import DEMO_COMMITTEE_EMAIL, DEMO_COMMITTEE_PASSWORD, seed
from backend.db.tables import FeynmanSession, User
from backend.main import app
from backend.security import AuthConfigError, check_auth_config, create_access_token

PUBLIC_ROUTES = {("POST", "/api/auth/register"), ("POST", "/api/auth/login"), ("GET", "/")}


def _api_routes() -> list[tuple[str, str]]:
    """Every (method, path) the app serves, read from its OpenAPI schema, so
    routers included at any depth are covered."""
    routes = []
    for path, operations in app.openapi()["paths"].items():
        for method in operations:
            if (method.upper(), path) not in PUBLIC_ROUTES:
                routes.append((method.upper(), re.sub(r"\{[^}]+\}", "c-001", path)))
    return routes


def _register(client, email: str = "applicant@example.kz", **extra) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "correct-horse", "full_name": "Aigerim", **extra},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── 401: no token, bad token ───────────────────────────────────────


def test_every_route_is_guarded(client):
    """Walks the app, so a router added later without a guard fails here."""
    routes = _api_routes()
    assert len(routes) > 20
    for method, path in routes:
        response = client.request(method, path)
        assert response.status_code == 401, f"{method} {path} answered {response.status_code} without a token"
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/auth/me"),
        ("GET", "/api/candidates/"),
        ("POST", "/api/scoring/rank"),
        ("GET", "/api/analysis/video-analysis/status"),
        ("GET", "/api/feynman/topics"),
    ],
)
def test_each_router_rejects_a_missing_token(client, method, path):
    assert client.request(method, path).status_code == 401


def test_expired_token_is_rejected(client, auth_headers):
    user_id = client.get("/api/auth/me", headers=auth_headers("committee")).json()["id"]
    issued = datetime.now(UTC) - timedelta(minutes=settings.AUTH_TOKEN_TTL_MINUTES + 1)
    expired = create_access_token(user_id, "committee", now=issued)

    response = client.get("/api/candidates/", headers=_bearer(expired))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_forged_and_malformed_tokens_are_rejected(client, auth_headers):
    user_id = client.get("/api/auth/me", headers=auth_headers("admin")).json()["id"]
    now = datetime.now(UTC)
    claims = {"sub": user_id, "role": "admin", "iat": now, "exp": now + timedelta(hours=1)}
    forged = jwt.encode(claims, "another-secret-that-is-also-long-enough", algorithm="HS256")
    unsigned = jwt.encode(claims, key=None, algorithm="none")
    old_style = f"{user_id}:{now.timestamp()}:0123456789abcdef"

    for token in (forged, unsigned, old_style, "garbage"):
        assert client.get("/api/auth/me", headers=_bearer(token)).status_code == 401, token


def test_token_of_a_deleted_user_is_rejected(client, db):
    body = _register(client)
    with Session(db) as session:
        session.delete(session.get(User, body["user"]["id"]))
        session.commit()
    assert client.get("/api/auth/me", headers=_bearer(body["token"])).status_code == 401


def test_role_is_read_from_the_database_not_the_token(client, db):
    """A role change applies at once, not when the token expires: the same
    goes for a demotion, which is the case that matters."""
    body = _register(client)
    with Session(db) as session:
        session.get(User, body["user"]["id"]).role = "committee"
        session.commit()
    headers = _bearer(body["token"])  # still says role=applicant
    assert client.get("/api/candidates/", headers=headers).status_code == 200


# ── 403: wrong role, per router ────────────────────────────────────


@pytest.mark.parametrize(
    "role,method,path",
    [
        # candidates: staff list, applicants submit
        ("applicant", "GET", "/api/candidates/"),
        ("committee", "POST", "/api/candidates/"),
        # scoring and analysis: committee and admin only
        ("applicant", "POST", "/api/scoring/rank"),
        ("interviewer", "POST", "/api/scoring/rank"),
        ("applicant", "POST", "/api/scoring/override"),
        ("applicant", "GET", "/api/analysis/video-analysis/status"),
        ("interviewer", "POST", "/api/analysis/ai-detection/c-001"),
        # feynman: the teaching challenge is the applicant's
        ("committee", "POST", "/api/feynman/start"),
        ("committee", "POST", "/api/feynman/chat"),
        # auth: link-candidate is the applicant's
        ("committee", "POST", "/api/auth/link-candidate?candidate_id=c-001"),
    ],
)
def test_wrong_role_is_403(client, auth_headers, role, method, path):
    assert client.request(method, path, headers=auth_headers(role)).status_code == 403


def test_committee_reaches_scoring_and_analysis(client, auth_headers):
    headers = auth_headers("committee")
    ranked = client.post("/api/scoring/rank", headers=headers)
    assert ranked.status_code == 200
    assert len(ranked.json()) == 16
    assert client.get("/api/analysis/video-analysis/status", headers=headers).status_code == 200


def test_interviewer_reads_applications(client, auth_headers):
    headers = auth_headers("interviewer")
    assert client.get("/api/candidates/", headers=headers).status_code == 200
    assert client.get("/api/candidates/c-004", headers=headers).status_code == 200


# ── Object level: an applicant sees only their own record ──────────


def test_applicant_reads_only_their_own_record(client, auth_headers):
    headers = auth_headers("applicant", owns="c-003")
    assert client.get("/api/candidates/c-003", headers=headers).json()["id"] == "c-003"
    assert client.get("/api/candidates/c-004", headers=headers).status_code == 403
    # A missing id looks the same as someone else's: no probing which exist.
    assert client.get("/api/candidates/c-999", headers=headers).status_code == 403
    assert client.get("/api/feynman/score/c-003", headers=headers).status_code == 200
    assert client.get("/api/feynman/score/c-004", headers=headers).status_code == 403


def test_applicant_without_an_application_reads_nothing(client, auth_headers):
    headers = auth_headers("applicant")
    assert client.get("/api/candidates/c-001", headers=headers).status_code == 403


def test_applicant_cannot_teach_as_someone_else(client, auth_headers):
    """Rejected before any model call, so this stays offline."""
    headers = auth_headers("applicant", owns="c-003")
    response = client.post(
        "/api/feynman/start", json={"candidate_id": "c-004", "topic_id": "seasons"}, headers=headers
    )
    assert response.status_code == 403


def test_teaching_session_belongs_to_whoever_started_it(client, db, auth_headers):
    owner = client.get("/api/auth/me", headers=(owner_headers := auth_headers("applicant", owns="c-003"))).json()
    session_id = feynman_store.create_session(applicant_id_for("c-003"), owner["id"], "seasons", [], max_attempts=1)["id"]
    with Session(db) as session:
        session.get(FeynmanSession, session_id).exchange_count = 8
        session.commit()
    other = auth_headers("applicant", owns="c-004")

    chat = {"session_id": session_id, "message": "hi"}
    assert client.post("/api/feynman/chat", json=chat, headers=other).status_code == 404
    assert client.post(f"/api/feynman/finish?session_id={session_id}", headers=other).status_code == 404
    # The owner reaches the session (and hits its exchange limit, not a 404).
    assert client.post("/api/feynman/chat", json=chat, headers=owner_headers).status_code == 400


def test_one_application_per_account(client):
    from tests.test_db_core import _new_application

    headers = _bearer(_register(client)["token"])
    first = client.post("/api/candidates/", json=_new_application(), headers=headers)
    assert first.status_code == 201
    assert client.get(f"/api/candidates/{first.json()['id']}", headers=headers).status_code == 200
    assert client.post("/api/candidates/", json=_new_application(), headers=headers).status_code == 409


# ── Registration and passwords ─────────────────────────────────────


def test_registration_always_creates_an_applicant(client):
    body = _register(client, role="admin")
    assert body["user"]["role"] == "applicant"


def test_passwords_are_argon2_and_login_is_case_insensitive_on_email(client):
    _register(client, email="Mixed@Example.kz")
    stored = user_store.get_user_by_email("mixed@example.kz")
    assert stored["password_hash"].startswith("$argon2id$")
    assert "correct-horse" not in stored["password_hash"]

    login = client.post("/api/auth/login", json={"email": " MIXED@example.kz", "password": "correct-horse"})
    assert login.status_code == 200
    assert client.post("/api/auth/login", json={"email": "mixed@example.kz", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "nobody@example.kz", "password": "x"}).status_code == 401


def test_short_password_is_refused(client):
    response = client.post(
        "/api/auth/register", json={"email": "s@example.kz", "password": "short", "full_name": "S"}
    )
    assert response.status_code == 422


def test_pre_fnd05_sha256_hash_fails_cleanly(client, db):
    """Old hashes are not migrated; they must fail login, not crash it."""
    legacy = hashlib.sha256(b"invisionu-hackathon-secret-2026:password1").hexdigest()
    user_store.create_user("legacy@example.kz", legacy, "Legacy")
    response = client.post("/api/auth/login", json={"email": "legacy@example.kz", "password": "password1"})
    assert response.status_code == 401


# ── Demo account only under DEMO_MODE ──────────────────────────────


def _drop_demo_user(db) -> None:
    with Session(db) as session:
        for user in session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)):
            session.delete(user)
        session.commit()


def _demo_login(client):
    return client.post("/api/auth/login", json={"email": DEMO_COMMITTEE_EMAIL, "password": DEMO_COMMITTEE_PASSWORD})


def test_demo_account_is_not_seeded_without_demo_mode(client, db, monkeypatch):
    _drop_demo_user(db)
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert seed().demo_user_added is False
    assert user_store.get_user_by_email(DEMO_COMMITTEE_EMAIL) is None
    assert _demo_login(client).status_code == 401


def test_demo_account_is_seeded_and_logs_in_under_demo_mode(client, db, monkeypatch):
    _drop_demo_user(db)
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    assert seed().demo_user_added is True
    login = _demo_login(client)
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "committee"


def test_leftover_demo_account_stops_working_when_demo_mode_is_off(client, db, monkeypatch):
    """A database seeded in demo mode keeps the row; the login must still fail."""
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    seed()
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert user_store.get_user_by_email(DEMO_COMMITTEE_EMAIL) is not None
    assert _demo_login(client).status_code == 401


# ── Configuration ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "secret,demo_mode,message",
    [
        ("", True, "AUTH_SECRET is not set"),
        ("too-short", True, "at least 32"),
        ("dev-only-invisionu-local-secret-not-for-production", False, "only accepted with DEMO_MODE=1"),
    ],
)
def test_unusable_auth_secret_is_refused(monkeypatch, secret, demo_mode, message):
    monkeypatch.setattr(settings, "AUTH_SECRET", secret)
    monkeypatch.setattr(settings, "DEMO_MODE", demo_mode)
    with pytest.raises(AuthConfigError, match=message):
        check_auth_config()


def test_dev_secret_is_accepted_under_demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_SECRET", "dev-only-invisionu-local-secret-not-for-production")
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    check_auth_config()


def test_app_refuses_to_start_without_auth_secret(db, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_SECRET", "")
    with pytest.raises(AuthConfigError):
        with TestClient(app):
            pass


def test_cors_allows_only_listed_origins(client):
    allowed = settings.CORS_ORIGINS[0]
    preflight = {"Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"}

    ok = client.options("/api/candidates/", headers={"Origin": allowed, **preflight})
    assert ok.headers.get("access-control-allow-origin") == allowed

    evil = client.options("/api/candidates/", headers={"Origin": "https://evil.example", **preflight})
    assert "access-control-allow-origin" not in evil.headers
