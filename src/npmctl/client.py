from __future__ import annotations

from typing import Any

import httpx

from .errors import ApiError, ConfigError, NotFoundError


class NpmClient:
    def __init__(self, base_url: str, token: str | None = None, verify: bool = True, timeout: float = 20):
        if not base_url:
            raise ConfigError("NPM URL is not configured. Run: npmctl config set-url URL")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = httpx.Client(base_url=self.base_url + "/api", verify=verify, timeout=timeout)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def request(self, method: str, path: str, json_data: Any | None = None, auth: bool = True) -> Any:
        headers = self._headers() if auth else {}
        try:
            resp = self.client.request(method, path, json=json_data, headers=headers)
        except httpx.HTTPError as exc:
            raise ApiError(str(exc)) from exc
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise ApiError(f"{method} {path} failed: HTTP {resp.status_code}: {detail}")
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return resp.text

    def login(self, identity: str, secret: str) -> dict[str, Any]:
        return self.request("POST", "/tokens", {"identity": identity, "secret": secret}, auth=False)

    def status(self) -> dict[str, Any]:
        return self.request("GET", "/", auth=False)

    def schema(self) -> dict[str, Any]:
        return self.request("GET", "/schema", auth=False)

    def list_proxy_hosts(self) -> list[dict[str, Any]]:
        return self.request("GET", "/nginx/proxy-hosts")

    def get_proxy_host(self, host_id: int) -> dict[str, Any]:
        return self.request("GET", f"/nginx/proxy-hosts/{host_id}")

    def create_proxy_host(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/nginx/proxy-hosts", payload)

    def update_proxy_host(self, host_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("PUT", f"/nginx/proxy-hosts/{host_id}", payload)

    def delete_proxy_host(self, host_id: int) -> Any:
        return self.request("DELETE", f"/nginx/proxy-hosts/{host_id}")

    def enable_proxy_host(self, host_id: int) -> Any:
        return self.request("POST", f"/nginx/proxy-hosts/{host_id}/enable")

    def disable_proxy_host(self, host_id: int) -> Any:
        return self.request("POST", f"/nginx/proxy-hosts/{host_id}/disable")

    def list_certificates(self) -> list[dict[str, Any]]:
        return self.request("GET", "/nginx/certificates")


def resolve_proxy(hosts: list[dict[str, Any]], identifier: str) -> dict[str, Any]:
    if identifier.isdigit():
        host_id = int(identifier)
        for host in hosts:
            if host.get("id") == host_id:
                return host
        raise NotFoundError(f"Proxy host id not found: {identifier}")
    matches = [h for h in hosts if identifier in h.get("domain_names", [])]
    if not matches:
        raise NotFoundError(f"Proxy host domain not found: {identifier}")
    if len(matches) > 1:
        raise ApiError(f"Multiple proxy hosts matched domain: {identifier}")
    return matches[0]
