from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from npmctl.command_help import print_help_if_no_subcommand
from npmctl.config import Config, config_path, normalize_base_url

app = typer.Typer(help="Manage local npmctl configuration")
profile_app = typer.Typer(help="Manage NPM instance profiles")
app.add_typer(profile_app, name="profile")
console = Console()


@app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context):
    print_help_if_no_subcommand(ctx)


@profile_app.callback(invoke_without_command=True)
def profile_callback(ctx: typer.Context):
    print_help_if_no_subcommand(ctx)


@app.command("set-url")
def set_url(url: str):
    cfg = Config.load()
    cfg.url = normalize_base_url(url)
    cfg.save()
    console.print(f"Saved URL for profile '{cfg.current_profile}' to {config_path()}: {cfg.url}")


@app.command("get")
def get_config(all_profiles: bool = typer.Option(False, "--all", help="Show all profiles, with secrets redacted")):
    cfg = Config.load()
    console.print(cfg.display(include_profiles=all_profiles))


@app.command("set-tls-verify")
def set_tls_verify(enabled: bool):
    cfg = Config.load()
    cfg.verify_tls = enabled
    cfg.save()
    console.print(f"profile={cfg.current_profile} verify_tls={enabled}")


@profile_app.command("list")
def profile_list():
    cfg = Config.load()
    table = Table(title="npmctl profiles")
    for col in ["Current", "Name", "URL", "Identity", "Token", "Password", "TLS Verify"]:
        table.add_column(col)
    for name, profile in cfg.profiles.items():
        table.add_row(
            "*" if name == cfg.current_profile else "",
            name,
            str(profile.get("url") or ""),
            str(profile.get("identity") or ""),
            "yes" if profile.get("token") else "no",
            "yes" if profile.get("password") else "no",
            str(profile.get("verify_tls", True)),
        )
    console.print(table)


@profile_app.command("add")
def profile_add(
    name: str,
    url: str = typer.Option(None, "--url", help="NPM base URL"),
    use: bool = typer.Option(False, "--use", help="Switch to this profile after creating it"),
    tls_verify: bool = typer.Option(True, "--tls-verify/--no-tls-verify"),
):
    cfg = Config.load()
    cfg.add_profile(name, url=url, verify_tls=tls_verify, use=use)
    cfg.save()
    console.print(f"Added profile '{name}'")


@profile_app.command("use")
def profile_use(name: str):
    cfg = Config.load()
    cfg.use_profile(name)
    cfg.save()
    console.print(f"Current profile: {name}")


@profile_app.command("current")
def profile_current():
    cfg = Config.load()
    console.print(cfg.current_profile)


@profile_app.command("remove")
def profile_remove(name: str, yes: bool = typer.Option(False, "--yes", "-y")):
    cfg = Config.load()
    if not yes:
        typer.confirm(f"Remove profile '{name}' and its saved token/password?", abort=True)
    cfg.remove_profile(name)
    cfg.save()
    console.print(f"Removed profile '{name}'")
