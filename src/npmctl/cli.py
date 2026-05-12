from __future__ import annotations

import sys

import typer
from rich.console import Console

from npmctl import __version__
from npmctl.command_help import print_help_if_no_subcommand
from npmctl.commands import auth, cert, config_cmd, proxy
from npmctl.context import make_client
from npmctl.errors import NpmctlError

app = typer.Typer(help="Nginx Proxy Manager CLI")
app.add_typer(config_cmd.app, name="config")
app.add_typer(auth.app, name="auth")
app.add_typer(cert.app, name="cert")
app.add_typer(proxy.app, name="proxy")
console = Console(stderr=True)


@app.callback(invoke_without_command=True)
def cli_callback(ctx: typer.Context):
    print_help_if_no_subcommand(ctx)


@app.command()
def version():
    """Print npmctl version."""
    typer.echo(__version__)


@app.command()
def doctor():
    """Check connectivity to the configured NPM API."""
    cfg, client = make_client(require_token=False)
    data = client.status()
    Console().print({"url": cfg.url, "api": data})


def main():
    try:
        app()
    except NpmctlError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
