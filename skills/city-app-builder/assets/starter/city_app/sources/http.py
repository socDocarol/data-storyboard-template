"""Bounded JSON GET requests with explicit pagination and environment auth."""

from __future__ import annotations

import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .common import MAX_BYTES, SourceError, row_limit


def validate_url(url: str):
    try:
        parts = urlsplit(url)
        parts.port
    except (ValueError, TypeError) as error:
        raise SourceError("Use a valid HTTPS source URL.") from error
    if parts.username or parts.password or not parts.hostname or parts.fragment:
        raise SourceError("Source URLs must not contain credentials or fragments.")
    if parts.scheme != "https" and not (
        parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost", "::1")
    ):
        raise SourceError(
            "Use HTTPS. Plain HTTP is allowed only for a local example server."
        )
    credential_keys = {
        "token",
        "accesstoken",
        "refreshtoken",
        "idtoken",
        "apikey",
        "key",
        "password",
        "passwd",
        "pwd",
        "secret",
        "clientsecret",
        "clientkey",
        "accesskey",
        "accesskeyid",
        "subscriptionkey",
        "ocpapimsubscriptionkey",
        "sig",
        "signature",
        "auth",
        "authorization",
        "credential",
        "credentials",
        "sas",
        "sastoken",
        "xamzsignature",
        "xamzcredential",
        "xgoogsignature",
        "xgoogcredential",
    }
    if any(
        re.sub(r"[^a-z0-9]", "", key.lower()) in credential_keys
        for key, _ in parse_qsl(parts.query)
    ):
        raise SourceError(
            "Keep credentials out of URLs. Configure an environment-backed auth header."
        )
    return parts


def with_params(url: str, params: dict) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(params)
    return urlunsplit(parts._replace(query=urlencode(query)))


def at_path(payload, path: str):
    if not isinstance(path, str):
        raise SourceError("JSON paths must be dot-separated object keys.")
    for key in path.split(".") if path else ():
        if not isinstance(payload, dict) or key not in payload:
            raise SourceError("The JSON response does not contain the configured path.")
        payload = payload[key]
    return payload


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class JsonClient:
    """One fetch budget shared across metadata and all result pages."""

    def __init__(self, auth: dict | None = None):
        self.started = time.monotonic()
        self.bytes_read = 0
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "DataStoryboardTemplate/0.6",
        }
        if auth:
            variable = auth.get("env")
            token = os.environ.get(variable, "") if isinstance(variable, str) else ""
            if not token:
                raise SourceError(
                    "The configured API credential environment variable is not set."
                )
            header = auth.get("header", "Authorization")
            prefix = auth.get("prefix", "Bearer ")
            if not isinstance(header, str) or header.lower() not in (
                "authorization",
                "x-api-key",
                "api-key",
            ):
                raise SourceError(
                    "Use Authorization, X-API-Key, or Api-Key for the auth header."
                )
            if not isinstance(prefix, str) or any(
                char in prefix + token for char in "\r\n"
            ):
                raise SourceError("The API credential is not a valid header value.")
            self.headers[header] = prefix + token
        self.opener = build_opener(_NoRedirect())

    def get(self, url: str, params: dict | None = None, *, post: bool = False):
        validate_url(url)
        remaining = 60 - (time.monotonic() - self.started)
        if remaining <= 0:
            raise SourceError(
                "The source exceeded the 60-second fetch budget. Narrow the request."
            )
        request = Request(
            with_params(url, params) if params and not post else url,
            data=urlencode(params).encode() if post else None,
            headers=self.headers,
        )
        try:
            with self.opener.open(request, timeout=min(15, remaining)) as response:
                if response.headers.get("Content-Encoding", "identity") != "identity":
                    raise SourceError("The endpoint must return uncompressed JSON.")
                chunks = []
                while chunk := response.read(
                    min(65_536, MAX_BYTES - self.bytes_read + 1)
                ):
                    self.bytes_read += len(chunk)
                    if self.bytes_read > MAX_BYTES:
                        raise SourceError(
                            "The source exceeded the 10 MB fetch budget. Narrow the request."
                        )
                    if time.monotonic() - self.started > 60:
                        raise SourceError(
                            "The source exceeded the 60-second fetch budget."
                        )
                    chunks.append(chunk)
                return json.loads(b"".join(chunks).decode("utf-8-sig"))
        except HTTPError as error:
            if 300 <= error.code < 400:
                raise SourceError(
                    "The endpoint redirected. Configure its final HTTPS URL; credentials were not forwarded."
                ) from error
            raise SourceError(
                f"The source returned HTTP {error.code}. Check access and the endpoint configuration."
            ) from error
        except (URLError, TimeoutError, OSError, ValueError) as error:
            if isinstance(error, SourceError):
                raise
            raise SourceError(
                "The endpoint could not be read as JSON. Check connectivity, TLS, and the response format."
            ) from error


def read_rows(config: dict) -> list[dict]:
    url = config.get("url", "")
    origin = validate_url(url)
    client = JsonClient(config.get("auth"))
    pagination = config.get("pagination", {"mode": "none"})
    mode = pagination.get("mode", "none")
    if mode not in ("none", "next", "page", "offset"):
        raise SourceError("pagination.mode must be none, next, page, or offset.")
    size = pagination.get("page_size", 500)
    if type(size) is not int or not 1 <= size <= 2000:
        raise SourceError("pagination.page_size must be between 1 and 2000.")
    position = pagination.get("start", 1 if mode == "page" else 0)
    if type(position) is not int or position < 0:
        raise SourceError("pagination.start must be a nonnegative integer.")
    rows, visited = [], set()
    for _ in range(100):
        if mode in ("page", "offset"):
            url = with_params(
                url,
                {
                    pagination.get("parameter", mode): position,
                    pagination.get("size_parameter", "limit"): size,
                },
            )
        if url in visited:
            raise SourceError(
                "The API pagination repeated a page. No partial data was loaded."
            )
        visited.add(url)
        payload = client.get(url)
        page = at_path(payload, config.get("records_path", ""))
        if not isinstance(page, list) or any(not isinstance(row, dict) for row in page):
            raise SourceError(
                "The configured records_path must identify an array of record objects."
            )
        if len(rows) + len(page) > row_limit(config):
            raise SourceError(
                "The API exceeds max_rows. Narrow the request; no partial totals were loaded."
            )
        rows.extend(page)
        if mode == "none":
            return rows
        if mode == "next":
            next_url = at_path(payload, pagination.get("next_path", "next"))
            if next_url in (None, ""):
                return rows
            if not isinstance(next_url, str):
                raise SourceError("The next-page field must be a URL or null.")
            url = urljoin(url, next_url)
            following = validate_url(url)
            if (following.scheme, following.hostname, following.port) != (
                origin.scheme,
                origin.hostname,
                origin.port,
            ):
                raise SourceError(
                    "The next page has a different origin. Credentials were not forwarded."
                )
        else:
            if not page:
                return rows
            position += 1 if mode == "page" else len(page)
    raise SourceError(
        "The API exceeded 100 pages. Narrow the request; no partial data was loaded."
    )
