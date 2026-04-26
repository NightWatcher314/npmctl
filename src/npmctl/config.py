from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

APP_NAME = "npmctl"
DEFAULT_PROFILE = "default"


def config_path() -> Path:
    override = os.environ.get("NPMCTL_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path(user_config_dir(APP_NAME)) / "config.json"


def normalize_base_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


@dataclass
class Config:
    current_profile: str = DEFAULT_PROFILE
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        path = config_path()
        data: dict[str, Any] = {}
        if path.exists():
            data = json.loads(path.read_text())

        # Backward-compatible migration from the original single-instance config.
        if "profiles" not in data:
            profile = {
                "url": data.get("url"),
                "token": data.get("token"),
                "identity": data.get("identity"),
                "password": data.get("password"),
                "verify_tls": data.get("verify_tls", True),
            }
            data = {
                "current_profile": data.get("current_profile", DEFAULT_PROFILE),
                "profiles": {data.get("current_profile", DEFAULT_PROFILE): profile},
            }

        current = os.environ.get("NPMCTL_PROFILE") or data.get("current_profile") or DEFAULT_PROFILE
        profiles = data.get("profiles") or {}
        profiles.setdefault(current, {"verify_tls": True})
        cfg = cls(current_profile=current, profiles=profiles, raw=data)

        # Environment overrides apply only to the active in-memory profile.
        active = cfg.active
        if os.environ.get("NPMCTL_URL"):
            active["url"] = normalize_base_url(os.environ["NPMCTL_URL"])
        if os.environ.get("NPMCTL_TOKEN"):
            active["token"] = os.environ["NPMCTL_TOKEN"]
        if os.environ.get("NPMCTL_IDENTITY"):
            active["identity"] = os.environ["NPMCTL_IDENTITY"]
        if os.environ.get("NPMCTL_PASSWORD"):
            active["password"] = os.environ["NPMCTL_PASSWORD"]
        if os.environ.get("NPMCTL_INSECURE") in {"1", "true", "yes"}:
            active["verify_tls"] = False
        return cfg

    @property
    def active(self) -> dict[str, Any]:
        return self.profiles.setdefault(self.current_profile, {"verify_tls": True})

    @property
    def url(self) -> str | None:
        return self.active.get("url")

    @url.setter
    def url(self, value: str | None) -> None:
        self.active["url"] = normalize_base_url(value) if value else None

    @property
    def token(self) -> str | None:
        return self.active.get("token")

    @token.setter
    def token(self, value: str | None) -> None:
        self.active["token"] = value

    @property
    def identity(self) -> str | None:
        return self.active.get("identity")

    @identity.setter
    def identity(self, value: str | None) -> None:
        self.active["identity"] = value

    @property
    def password(self) -> str | None:
        return self.active.get("password")

    @password.setter
    def password(self, value: str | None) -> None:
        self.active["password"] = value

    @property
    def verify_tls(self) -> bool:
        return self.active.get("verify_tls", True)

    @verify_tls.setter
    def verify_tls(self, value: bool) -> None:
        self.active["verify_tls"] = value

    def use_profile(self, name: str) -> None:
        self.current_profile = name
        self.profiles.setdefault(name, {"verify_tls": True})

    def add_profile(self, name: str, url: str | None = None, verify_tls: bool = True, use: bool = False) -> None:
        self.profiles[name] = {"url": normalize_base_url(url) if url else None, "verify_tls": verify_tls}
        if use:
            self.current_profile = name

    def remove_profile(self, name: str) -> None:
        if name in self.profiles:
            del self.profiles[name]
        if self.current_profile == name:
            self.current_profile = next(iter(self.profiles), DEFAULT_PROFILE)
            self.profiles.setdefault(self.current_profile, {"verify_tls": True})

    def save(self) -> None:
        path = config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "current_profile": self.current_profile,
            "profiles": self.profiles,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def display(self, include_profiles: bool = False) -> dict[str, Any]:
        def redact_profile(p: dict[str, Any]) -> dict[str, Any]:
            return {
                "url": p.get("url"),
                "identity": p.get("identity"),
                "has_token": bool(p.get("token")),
                "has_password": bool(p.get("password")),
                "verify_tls": p.get("verify_tls", True),
            }
        data = {
            "path": str(config_path()),
            "current_profile": self.current_profile,
            **redact_profile(self.active),
        }
        if include_profiles:
            data["profiles"] = {name: redact_profile(profile) for name, profile in self.profiles.items()}
        return data
