import json
import logging
import time
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Cached database URL: fetched once at startup, reused until a connection
# built from it fails — then re-fetched (with retries) to pick up a changed
# upstream URL.
_cached_database_url: str | None = None


class DatabaseUrlUnavailable(RuntimeError):
    """Raised when the discovery endpoint can't be reached or returns a bad response."""

    pass


def _extract_database_url(payload: str, settings: Settings) -> str:
    """Pull the database URL out of a plain-text or JSON response body."""
    value = payload.strip()
    if not value:
        raise ValueError("empty response")

    try:
        parsed = json.loads(value)
    except JSONDecodeError:
        parsed = value

    if isinstance(parsed, str):
        database_url = parsed.strip()
    elif isinstance(parsed, dict):
        database_url = ""
        for key in ("database_url", "db_url", "url", "tunnel_url"):
            candidate = parsed.get(key)
            if isinstance(candidate, str) and candidate.strip():
                database_url = candidate.strip()
                break
    else:
        database_url = ""

    if not database_url:
        raise ValueError("response did not contain a database URL")
    if "://" not in database_url:
        raise ValueError("database URL is not a valid connection URL")

    database_url = _build_url_from_tunnel(database_url, settings)
    return _ensure_psycopg3_scheme(database_url)


def _ensure_psycopg3_scheme(database_url: str) -> str:
    """Normalize tunnel/provider URLs into a SQLAlchemy psycopg 3 URL.

    The app installs psycopg[binary] (v3), but SQLAlchemy defaults to the
    psycopg2 driver for bare `postgresql://` URLs. Third-party providers
    (Supabase, Neon, etc.) hand out plain `postgresql://` URLs, and tunnel
    endpoints may return `tcp://host:port` (no credentials/database) —
    rewrite both into `postgresql+psycopg://` before handing them to
    SQLAlchemy.
    """
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _build_url_from_tunnel(
    tunnel_url: str, settings: Settings
) -> str:
    """Expand a bare tcp://host:port tunnel URL into a full Postgres URL.

    Tunnel endpoints (e.g. pinggy) expose the database as tcp://host:port
    with no credentials or database name; those come from settings
    (DATABASE_USER / DATABASE_PASSWORD / DATABASE_NAME).
    """
    if not tunnel_url.startswith("tcp://"):
        return tunnel_url

    from urllib.parse import quote

    rest = tunnel_url.removeprefix("tcp://")  # host:port
    user = quote(settings.database_user, safe="")
    password = quote(settings.database_password, safe="")
    return f"postgresql+psycopg://{user}:{password}@{rest}/{settings.database_name}"


def _fetch_database_url_from_endpoint(settings: Settings) -> str:
    """Single fetch attempt against DATABASE_URL_ENDPOINT."""
    headers = {"Accept": "application/json, text/plain"}
    if settings.database_url_endpoint_key:
        headers["X-API-Key"] = settings.database_url_endpoint_key
    request = Request(
        settings.database_url_endpoint,
        headers=headers,
    )

    try:
        with urlopen(request, timeout=settings.database_url_timeout_seconds) as response:
            payload = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise DatabaseUrlUnavailable(
            f"Unable to fetch the database URL from {settings.database_url_endpoint}"
        ) from exc

    try:
        return _extract_database_url(payload, settings)
    except ValueError as exc:
        raise DatabaseUrlUnavailable(
            f"Invalid database URL response from {settings.database_url_endpoint}"
        ) from exc


def _fetch_database_url_with_retry(settings: Settings, attempts: int = 3) -> str:
    """Fetch from the endpoint, retrying up to `attempts` times with a short backoff."""
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _fetch_database_url_from_endpoint(settings)
        except DatabaseUrlUnavailable as exc:
            last_exc = exc
            logger.warning(
                "Database URL fetch attempt %d/%d failed: %s",
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                time.sleep(0.5 * attempt)
    raise DatabaseUrlUnavailable(
        f"Could not fetch the database URL after {attempts} attempts"
    ) from last_exc


def resolve_database_url(settings: Settings | None = None) -> str:
    """Return the current database URL.

    Strategy:
    1. First call fetches from DATABASE_URL_ENDPOINT and caches the result.
    2. Subsequent calls reuse the cache — no HTTP round-trip per operation.
    3. Callers that hit a connection failure invoke invalidate_cached_database_url()
       and retry; the next resolve re-fetches (3 attempts) to pick up a changed
       upstream URL.
    4. If the endpoint is unreachable after all retries, DATABASE_URL is used
       as a last-resort fallback; with no fallback configured, the error
       propagates as a critical failure.
    """
    global _cached_database_url
    settings = settings or get_settings()

    if _cached_database_url is not None:
        return _cached_database_url

    try:
        _cached_database_url = _fetch_database_url_with_retry(settings)
    except DatabaseUrlUnavailable:
        if settings.database_url:
            logger.warning(
                "Discovery endpoint unavailable; falling back to DATABASE_URL"
            )
            _cached_database_url = _ensure_psycopg3_scheme(
                settings.database_url.strip()
            )
        else:
            logger.critical(
                "No database URL available: endpoint failed after retries and "
                "no DATABASE_URL fallback is configured"
            )
            raise
    return _cached_database_url


def invalidate_cached_database_url() -> None:
    """Drop the cached URL so the next resolve re-fetches from the endpoint.

    Call this when a connection built from the cached URL fails — the upstream
    database URL may have changed.
    """
    global _cached_database_url
    _cached_database_url = None
