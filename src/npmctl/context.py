from __future__ import annotations

from .client import NpmClient
from .config import Config


def make_client(require_token: bool = True) -> tuple[Config, NpmClient]:
    cfg = Config.load()
    token = cfg.token if require_token else None
    return cfg, NpmClient(cfg.url or "", token=token, verify=cfg.verify_tls)
