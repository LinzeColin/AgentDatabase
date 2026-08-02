from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

import jwt


class AccessVerificationError(RuntimeError):
    pass


def _team_domain(value: str) -> str:
    raw = value.strip().rstrip("/")
    if not raw:
        raise AccessVerificationError("缺少 MEMORY_ATLAS_CF_ACCESS_TEAM_DOMAIN")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
        raise AccessVerificationError("Cloudflare Access team domain 必须是完整 HTTPS origin")
    return f"https://{parsed.netloc}"


class CloudflareAccessVerifier:
    """Verify the signed Access application token, issuer and exact application AUD."""

    def __init__(
        self,
        team_domain: str,
        audience: str,
        key_resolver: Callable[[str], Any] | None = None,
    ) -> None:
        self.team_domain = _team_domain(team_domain)
        self.audience = audience.strip()
        if not self.audience:
            raise AccessVerificationError("缺少 MEMORY_ATLAS_CF_ACCESS_AUD")
        if key_resolver is None:
            jwks = jwt.PyJWKClient(
                f"{self.team_domain}/cdn-cgi/access/certs",
                cache_keys=True,
                lifespan=3600,
            )
            self._key_resolver = lambda token: jwks.get_signing_key_from_jwt(token).key
        else:
            self._key_resolver = key_resolver

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "CloudflareAccessVerifier":
        values = dict(os.environ if env is None else env)
        return cls(
            values.get("MEMORY_ATLAS_CF_ACCESS_TEAM_DOMAIN", ""),
            values.get("MEMORY_ATLAS_CF_ACCESS_AUD", ""),
        )

    def verify(self, token: str) -> dict[str, Any]:
        assertion = token.strip()
        if not assertion or len(assertion) > 16 * 1024:
            raise AccessVerificationError("Access JWT 缺失或长度不合法")
        try:
            key = self._key_resolver(assertion)
            payload = jwt.decode(
                assertion,
                key=key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.team_domain,
                leeway=30,
                options={"require": ["exp", "iat", "iss", "aud"]},
            )
        except Exception as exc:
            raise AccessVerificationError("Access JWT 签名、issuer、audience 或有效期校验失败") from exc
        if not isinstance(payload, dict):
            raise AccessVerificationError("Access JWT payload 不是 object")
        return payload
