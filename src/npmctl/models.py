from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .errors import ConfigError


@dataclass(frozen=True)
class Target:
    scheme: str
    host: str
    port: int
    path: str = ""


def parse_target(value: str) -> Target:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ConfigError("--to must be an http:// or https:// URL")
    if not parsed.hostname:
        raise ConfigError("--to must include a host")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or ""
    if parsed.params or parsed.query or parsed.fragment:
        raise ConfigError("--to must not include params, query, or fragment")
    return Target(parsed.scheme, parsed.hostname, port, path)


def wildcard_matches(pattern: str, domain: str) -> bool:
    pattern = pattern.lower().strip()
    domain = domain.lower().strip()
    if pattern == domain:
        return True
    if pattern.startswith("*."):
        suffix = pattern[1:]  # .example.com
        return domain.endswith(suffix) and domain.count(".") == suffix.count(".")
    return False
