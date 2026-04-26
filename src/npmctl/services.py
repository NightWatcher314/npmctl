from __future__ import annotations

from copy import deepcopy
from typing import Any

from .client import NpmClient, resolve_proxy
from .errors import ApiError, NotFoundError
from .models import Target, parse_target, wildcard_matches

ALLOWED_PROXY_FIELDS = {
    "domain_names",
    "forward_scheme",
    "forward_host",
    "forward_port",
    "certificate_id",
    "ssl_forced",
    "hsts_enabled",
    "hsts_subdomains",
    "trust_forwarded_proto",
    "http2_support",
    "block_exploits",
    "caching_enabled",
    "allow_websocket_upgrade",
    "access_list_id",
    "advanced_config",
    "enabled",
    "meta",
    "locations",
}

ALLOWED_LOCATION_FIELDS = {
    "id",
    "path",
    "forward_scheme",
    "forward_host",
    "forward_port",
    "forward_path",
    "advanced_config",
}


def sanitize_location(location: dict[str, Any]) -> dict[str, Any]:
    return {k: deepcopy(v) for k, v in location.items() if k in ALLOWED_LOCATION_FIELDS and v is not None}


def sanitize_proxy_payload(host: dict[str, Any]) -> dict[str, Any]:
    payload = {k: deepcopy(v) for k, v in host.items() if k in ALLOWED_PROXY_FIELDS}
    payload["locations"] = [sanitize_location(loc) for loc in payload.get("locations") or []]
    payload.setdefault("access_list_id", 0)
    payload.setdefault("certificate_id", 0)
    payload.setdefault("ssl_forced", False)
    payload.setdefault("caching_enabled", False)
    payload.setdefault("block_exploits", False)
    payload.setdefault("allow_websocket_upgrade", True)
    payload.setdefault("http2_support", True)
    payload.setdefault("hsts_enabled", False)
    payload.setdefault("hsts_subdomains", False)
    payload.setdefault("trust_forwarded_proto", False)
    payload.setdefault("advanced_config", "")
    payload.setdefault("enabled", True)
    return payload


def build_new_proxy_payload(
    domains: list[str],
    target: Target,
    *,
    certificate_id: int = 0,
    ssl_forced: bool = False,
    websocket: bool = True,
    http2: bool = True,
    block_exploits: bool = False,
    advanced_config: str = "",
) -> dict[str, Any]:
    return {
        "domain_names": domains,
        "forward_scheme": target.scheme,
        "forward_host": target.host,
        "forward_port": target.port,
        "access_list_id": 0,
        "certificate_id": certificate_id,
        "ssl_forced": ssl_forced,
        "caching_enabled": False,
        "block_exploits": block_exploits,
        "allow_websocket_upgrade": websocket,
        "http2_support": http2,
        "hsts_enabled": False,
        "hsts_subdomains": False,
        "trust_forwarded_proto": False,
        "advanced_config": advanced_config,
        "enabled": True,
        "locations": [],
    }


def cert_matches_domain(cert: dict[str, Any], domain: str) -> bool:
    return any(wildcard_matches(name, domain) for name in cert.get("domain_names", []))


def match_certificate(client: NpmClient, domain: str) -> dict[str, Any] | None:
    certs = client.list_certificates()
    matches = [c for c in certs if cert_matches_domain(c, domain)]
    if not matches:
        return None
    # Prefer wildcard certs, then lowest id for determinism.
    matches.sort(key=lambda c: (not any(str(d).startswith("*.") for d in c.get("domain_names", [])), c.get("id", 999999)))
    return matches[0]


def resolve_cert_id(client: NpmClient, domain: str, cert: str | None) -> int | None:
    if cert is None:
        return None
    if cert in {"none", "0"}:
        return 0
    if cert == "auto":
        match = match_certificate(client, domain)
        if not match:
            raise NotFoundError(f"No certificate matches {domain}")
        return int(match["id"])
    if cert.isdigit():
        return int(cert)
    raise ApiError("--cert must be 'auto', 'none', or a certificate id")


def apply_proxy(
    client: NpmClient,
    domain: str,
    target_url: str,
    *,
    cert: str | None = None,
    force_ssl: bool | None = None,
    websocket: bool | None = None,
    http2: bool | None = None,
    advanced_config: str | None = None,
    clear_advanced: bool = False,
    dry_run: bool = False,
) -> tuple[str, dict[str, Any]]:
    target = parse_target(target_url)
    hosts = client.list_proxy_hosts()
    existing = next((h for h in hosts if domain in h.get("domain_names", [])), None)
    cert_id = resolve_cert_id(client, domain, cert)

    if existing:
        full = client.get_proxy_host(int(existing["id"]))
        payload = sanitize_proxy_payload(full)
        payload["forward_scheme"] = target.scheme
        payload["forward_host"] = target.host
        payload["forward_port"] = target.port
        if cert_id is not None:
            payload["certificate_id"] = cert_id
        if force_ssl is not None:
            payload["ssl_forced"] = force_ssl
        if websocket is not None:
            payload["allow_websocket_upgrade"] = websocket
        if http2 is not None:
            payload["http2_support"] = http2
        if clear_advanced:
            payload["advanced_config"] = ""
        elif advanced_config is not None:
            payload["advanced_config"] = advanced_config
        if dry_run:
            return "update-dry-run", payload
        return "updated", client.update_proxy_host(int(existing["id"]), payload)

    payload = build_new_proxy_payload(
        [domain],
        target,
        certificate_id=cert_id or 0,
        ssl_forced=bool(force_ssl) if force_ssl is not None else bool(cert_id),
        websocket=True if websocket is None else websocket,
        http2=True if http2 is None else http2,
        advanced_config="" if advanced_config is None else advanced_config,
    )
    if clear_advanced:
        payload["advanced_config"] = ""
    if dry_run:
        return "create-dry-run", payload
    return "created", client.create_proxy_host(payload)


def set_host_advanced(client: NpmClient, identifier: str, config: str, dry_run: bool = False) -> dict[str, Any]:
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    payload = sanitize_proxy_payload(full)
    payload["advanced_config"] = config
    if dry_run:
        return payload
    return client.update_proxy_host(int(host["id"]), payload)


def find_location(host: dict[str, Any], path: str) -> dict[str, Any] | None:
    return next((loc for loc in host.get("locations") or [] if loc.get("path") == path), None)


def apply_location(client: NpmClient, identifier: str, path: str, target_url: str, *, advanced_config: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    payload = sanitize_proxy_payload(full)
    target = parse_target(target_url)
    locations = payload.setdefault("locations", [])
    loc = find_location(payload, path)
    if loc is None:
        loc = {"path": path}
        locations.append(loc)
    loc.update({
        "forward_scheme": target.scheme,
        "forward_host": target.host,
        "forward_port": target.port,
    })
    if target.path:
        loc["forward_path"] = target.path
    if advanced_config is not None:
        loc["advanced_config"] = advanced_config
    loc_clean = sanitize_location(loc)
    loc.clear(); loc.update(loc_clean)
    if dry_run:
        return payload
    return client.update_proxy_host(int(host["id"]), payload)


def set_location_advanced(client: NpmClient, identifier: str, path: str, config: str, dry_run: bool = False) -> dict[str, Any]:
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    payload = sanitize_proxy_payload(full)
    loc = find_location(payload, path)
    if loc is None:
        raise NotFoundError(f"Location not found on {identifier}: {path}")
    loc["advanced_config"] = config
    if dry_run:
        return payload
    return client.update_proxy_host(int(host["id"]), payload)
