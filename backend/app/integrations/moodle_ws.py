"""integrations/moodle_ws.py — Moodle Web Services async client (C-09).

Consumes the standard Moodle Web Services API to fetch enrolled users
and activities. Used by PadronService for on-demand and nightly syncs.

Design decisions (C-09 design.md D5):
- MoodleWSClient receives moodle_url and token at construction time (already
  decrypted by the caller). This allows easy mocking in tests without
  patching HTTP.
- Retry with exponential backoff (1s, 2s, 4s) for network errors ONLY.
  HTTP 4xx errors are not retried (they indicate bad credentials/config).
- MoodleWSError wraps any Moodle-side failure. The router maps it to 502.
- health_check() returns a bool — callers handle the failure, no exception.

Moodle WS API:
  Base URL:   {moodle_url}/webservice/rest/server.php
  Parameters: wstoken, wsfunction, moodlewsrestformat=json
"""

import asyncio
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Retry configuration (network errors only)
_MAX_RETRIES = 3
_RETRY_DELAYS = [1.0, 2.0, 4.0]  # seconds between attempts

# Moodle WS endpoint path
_WS_PATH = "/webservice/rest/server.php"


class MoodleWSError(Exception):
    """Raised when the Moodle Web Services call fails.

    Attributes:
        detail: Human-readable error description.
        status_code: HTTP status code, or None for network errors.
    """

    def __init__(self, detail: str, status_code: int | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass
class MoodleEnrolledUser:
    """A student enrolled in a Moodle course."""

    id: int
    username: str
    firstname: str
    lastname: str
    email: str
    fullname: str


class MoodleWSClient:
    """Async client for the Moodle Web Services REST API.

    Args:
        moodle_url: Base URL of the Moodle instance (no trailing slash).
        token: Moodle WS token (plaintext, decrypted by caller).
        timeout: HTTP request timeout in seconds. Default: 30.

    Usage:
        client = MoodleWSClient(moodle_url="https://moodle.example.com", token="abc123")
        users = await client.get_enrolled_users(course_id=42)
        ok = await client.health_check()
    """

    def __init__(
        self,
        moodle_url: str,
        token: str,
        timeout: float = 30.0,
    ) -> None:
        self._moodle_url = moodle_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    @property
    def _ws_url(self) -> str:
        return f"{self._moodle_url}{_WS_PATH}"

    async def _call_ws(
        self,
        wsfunction: str,
        params: dict | None = None,
    ) -> list | dict:
        """Make an authenticated call to Moodle WS with retry logic.

        Retries on network errors (ConnectError, TimeoutException) with
        exponential backoff. Does NOT retry on HTTP 4xx.

        Args:
            wsfunction: Moodle WS function name (e.g. 'core_enrol_get_enrolled_users').
            params: Additional query parameters.

        Returns:
            Parsed JSON response (list or dict).

        Raises:
            MoodleWSError: On HTTP 4xx, 5xx, or network failure after all retries.
        """
        query = {
            "wstoken": self._token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
        }
        if params:
            query.update(params)

        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as http:
                    response = await http.get(self._ws_url, params=query)

                # HTTP 4xx: bad credentials / config — do NOT retry
                if 400 <= response.status_code < 500:
                    raise MoodleWSError(
                        f"Moodle WS returned {response.status_code}: {response.text[:200]}",
                        status_code=response.status_code,
                    )

                # HTTP 5xx: server error — retryable
                if response.status_code >= 500:
                    last_error = MoodleWSError(
                        f"Moodle WS server error {response.status_code}",
                        status_code=response.status_code,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        delay = _RETRY_DELAYS[attempt]
                        logger.warning(
                            "Moodle WS attempt %d/%d failed (HTTP %d), retrying in %.1fs",
                            attempt + 1,
                            _MAX_RETRIES,
                            response.status_code,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    continue

                data = response.json()

                # Moodle returns {"exception": ..., "message": ...} for WS-level errors
                if isinstance(data, dict) and "exception" in data:
                    raise MoodleWSError(
                        f"Moodle WS exception: {data.get('message', 'unknown')}",
                        status_code=200,
                    )

                return data

            except MoodleWSError:
                raise  # propagate immediately (no retry for 4xx or WS exceptions)

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < _MAX_RETRIES - 1:
                    delay = _RETRY_DELAYS[attempt]
                    logger.warning(
                        "Moodle WS network error on attempt %d/%d: %s — retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)

            except httpx.HTTPError as exc:
                # Other HTTP errors are treated as network errors
                last_error = exc
                if attempt < _MAX_RETRIES - 1:
                    delay = _RETRY_DELAYS[attempt]
                    await asyncio.sleep(delay)

        raise MoodleWSError(
            f"Moodle WS unreachable after {_MAX_RETRIES} attempts: {last_error}",
        )

    async def get_enrolled_users(self, course_id: int) -> list[MoodleEnrolledUser]:
        """Fetch all users enrolled in a Moodle course.

        Args:
            course_id: Moodle course ID.

        Returns:
            List of MoodleEnrolledUser.

        Raises:
            MoodleWSError: On any Moodle WS failure.
        """
        data = await self._call_ws(
            wsfunction="core_enrol_get_enrolled_users",
            params={"courseid": course_id},
        )
        if not isinstance(data, list):
            raise MoodleWSError(
                f"Unexpected response type from Moodle WS (expected list, got {type(data).__name__})"
            )
        return [
            MoodleEnrolledUser(
                id=u.get("id", 0),
                username=u.get("username", ""),
                firstname=u.get("firstname", ""),
                lastname=u.get("lastname", ""),
                email=u.get("email", ""),
                fullname=u.get("fullname", ""),
            )
            for u in data
        ]

    async def health_check(self) -> bool:
        """Check if the Moodle WS endpoint is reachable and the token is valid.

        Returns:
            True if the check succeeds, False otherwise (never raises).
        """
        try:
            await self._call_ws(wsfunction="core_webservice_get_site_info")
            return True
        except (MoodleWSError, Exception):  # noqa: BLE001
            return False
