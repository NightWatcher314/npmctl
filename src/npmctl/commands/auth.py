from __future__ import annotations

import getpass
import os
import sys

import typer
from rich.console import Console

from npmctl.client import NpmClient
from npmctl.config import Config, normalize_base_url
from npmctl.context import make_client

app = typer.Typer(help="Authenticate to Nginx Proxy Manager")
console = Console()


@app.command("login")
def login(
    identity: str = typer.Option(None, "--identity", "-i", help="NPM username/email"),
    url: str = typer.Option(None, "--url", help="NPM base URL for the active profile"),
    password_stdin: bool = typer.Option(False, "--password-stdin", help="Read password from stdin"),
    save_password: bool = typer.Option(False, "--save-password", help="Save password in the active profile config"),
    use_saved_password: bool = typer.Option(True, "--use-saved-password/--no-use-saved-password", help="Reuse saved password when available"),
):
    cfg = Config.load()
    if url:
        cfg.url = normalize_base_url(url)
    if not cfg.url:
        cfg.url = normalize_base_url(typer.prompt("NPM URL"))
    identity = identity or cfg.identity or os.environ.get("NPMCTL_IDENTITY") or typer.prompt("Identity")

    if password_stdin:
        secret = sys.stdin.read().strip("\n")
    elif os.environ.get("NPMCTL_PASSWORD"):
        secret = os.environ["NPMCTL_PASSWORD"]
    elif use_saved_password and cfg.password:
        secret = cfg.password
    else:
        secret = getpass.getpass("Password: ")

    client = NpmClient(cfg.url, verify=cfg.verify_tls)
    token = client.login(identity, secret)["token"]
    cfg.identity = identity
    cfg.token = token
    if save_password:
        cfg.password = secret
    cfg.save()
    console.print(f"[green]Login OK[/green] profile={cfg.current_profile} saved_password={bool(cfg.password)}")


@app.command("status")
def status():
    cfg, client = make_client(require_token=False)
    data = client.status()
    console.print({
        "profile": cfg.current_profile,
        "url": cfg.url,
        "identity": cfg.identity,
        "has_token": bool(cfg.token),
        "has_password": bool(cfg.password),
        "api": data,
    })


@app.command("logout")
def logout(clear_password: bool = typer.Option(False, "--clear-password", help="Also remove saved password")):
    cfg = Config.load()
    cfg.token = None
    if clear_password:
        cfg.password = None
    cfg.save()
    console.print(f"Logged out locally from profile={cfg.current_profile}")


@app.command("forget-password")
def forget_password():
    cfg = Config.load()
    cfg.password = None
    cfg.save()
    console.print(f"Removed saved password for profile={cfg.current_profile}")
