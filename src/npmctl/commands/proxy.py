from __future__ import annotations

import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

from npmctl.client import resolve_proxy
from npmctl.context import make_client
from npmctl.output import dump
from npmctl.services import apply_location, apply_proxy, sanitize_proxy_payload, set_host_advanced, set_location_advanced

app = typer.Typer(help="Manage Proxy Hosts")
advanced_app = typer.Typer(help="Manage host-level advanced_config snippets")
location_app = typer.Typer(help="Manage custom locations")
location_advanced_app = typer.Typer(help="Manage location-level advanced_config snippets")
app.add_typer(advanced_app, name="advanced")
app.add_typer(location_app, name="location")
location_app.add_typer(location_advanced_app, name="advanced")
console = Console()


def read_snippet(value: str | None, file: Path | None, stdin_flag: bool, clear: bool = False) -> str | None:
    selected = sum(x is not None and x is not False for x in [value, file, stdin_flag, clear])
    if selected > 1:
        raise typer.BadParameter("Use only one of --advanced, --advanced-file/--file, --advanced-stdin/--stdin, --clear-advanced")
    if clear:
        return ""
    if value is not None:
        return value
    if file is not None:
        return file.read_text()
    if stdin_flag:
        return sys.stdin.read()
    return None


@app.command("list")
def list_hosts(output: str = typer.Option("table", "--output", "-o", help="table|json|yaml")):
    _, client = make_client()
    hosts = client.list_proxy_hosts()
    table = Table(title="Proxy Hosts")
    for col in ["ID", "Domains", "Target", "SSL", "Enabled"]:
        table.add_column(col)
    for h in hosts:
        target = f"{h.get('forward_scheme')}://{h.get('forward_host')}:{h.get('forward_port')}"
        table.add_row(str(h.get("id")), ", ".join(h.get("domain_names", [])), target, str(bool(h.get("certificate_id"))), str(h.get("enabled")))
    dump(hosts, output, table)


@app.command("get")
def get_host(identifier: str, output: str = typer.Option("yaml", "--output", "-o", help="table|json|yaml")):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    dump(full, output)


@app.command("apply")
def apply(
    domain: str,
    to: str = typer.Option(..., "--to", help="Target URL, e.g. http://192.168.1.2:8080"),
    cert: str = typer.Option(None, "--cert", help="auto|none|CERT_ID"),
    force_ssl: bool = typer.Option(None, "--force-ssl/--no-force-ssl", help="Set SSL forced"),
    websocket: bool = typer.Option(None, "--websocket/--no-websocket", help="Set websocket upgrade"),
    http2: bool = typer.Option(None, "--http2/--no-http2", help="Set HTTP/2 support"),
    advanced: str = typer.Option(None, "--advanced", help="Raw host-level advanced_config snippet"),
    advanced_file: Path = typer.Option(None, "--advanced-file", help="Read host-level advanced_config from file"),
    advanced_stdin: bool = typer.Option(False, "--advanced-stdin", help="Read host-level advanced_config from stdin"),
    clear_advanced: bool = typer.Option(False, "--clear-advanced", help="Clear host-level advanced_config"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    output: str = typer.Option("yaml", "--output", "-o", help="table|json|yaml"),
):
    _, client = make_client()
    snippet = read_snippet(advanced, advanced_file, advanced_stdin, clear_advanced)
    action, result = apply_proxy(client, domain, to, cert=cert, force_ssl=force_ssl, websocket=websocket, http2=http2, advanced_config=snippet, clear_advanced=clear_advanced, dry_run=dry_run)
    if output == "table":
        console.print(f"{action}: {result.get('id', domain)}")
    else:
        dump({"action": action, "proxy": result}, output)


@app.command("delete")
def delete(identifier: str, yes: bool = typer.Option(False, "--yes", "-y")):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    if not yes:
        typer.confirm(f"Delete proxy host {host.get('domain_names')}?", abort=True)
    client.delete_proxy_host(int(host["id"]))
    console.print("[green]Deleted[/green]")


@app.command("enable")
def enable(identifier: str):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    client.enable_proxy_host(int(host["id"]))
    console.print("[green]Enabled[/green]")


@app.command("disable")
def disable(identifier: str):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    client.disable_proxy_host(int(host["id"]))
    console.print("[green]Disabled[/green]")


@app.command("test")
def test(domain: str, path: str = typer.Option("/", "--path"), insecure: bool = typer.Option(False, "--insecure")):
    url = f"https://{domain}{path}"
    with httpx.Client(follow_redirects=False, verify=not insecure, timeout=15) as c:
        r = c.get(url)
    console.print({"url": url, "status_code": r.status_code, "location": r.headers.get("location"), "content_type": r.headers.get("content-type")})


@advanced_app.command("get")
def advanced_get(identifier: str):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    sys.stdout.write(full.get("advanced_config") or "")


@advanced_app.command("set")
def advanced_set(
    identifier: str,
    value: str = typer.Option(None, "--value", "--advanced"),
    file: Path = typer.Option(None, "--file", "-f"),
    stdin_flag: bool = typer.Option(False, "--stdin"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    output: str = typer.Option("yaml", "--output", "-o"),
):
    _, client = make_client()
    snippet = read_snippet(value, file, stdin_flag)
    if snippet is None:
        raise typer.BadParameter("Provide --value, --file, or --stdin")
    result = set_host_advanced(client, identifier, snippet, dry_run=dry_run)
    dump(result, output)


@advanced_app.command("clear")
def advanced_clear(identifier: str):
    _, client = make_client()
    set_host_advanced(client, identifier, "")
    console.print("[green]Cleared[/green]")


@location_app.command("list")
def location_list(identifier: str, output: str = typer.Option("yaml", "--output", "-o")):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    dump(full.get("locations") or [], output)


@location_app.command("apply")
def location_apply(
    identifier: str,
    path: str,
    to: str = typer.Option(..., "--to"),
    advanced: str = typer.Option(None, "--advanced"),
    advanced_file: Path = typer.Option(None, "--advanced-file"),
    advanced_stdin: bool = typer.Option(False, "--advanced-stdin"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    output: str = typer.Option("yaml", "--output", "-o"),
):
    _, client = make_client()
    snippet = read_snippet(advanced, advanced_file, advanced_stdin)
    result = apply_location(client, identifier, path, to, advanced_config=snippet, dry_run=dry_run)
    dump(result, output)


@location_app.command("delete")
def location_delete(identifier: str, path: str, yes: bool = typer.Option(False, "--yes", "-y")):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    payload = sanitize_proxy_payload(full)
    payload["locations"] = [loc for loc in payload.get("locations", []) if loc.get("path") != path]
    if len(payload["locations"]) == len(full.get("locations") or []):
        raise typer.BadParameter(f"Location not found: {path}")
    if not yes:
        typer.confirm(f"Delete location {path} from {identifier}?", abort=True)
    client.update_proxy_host(int(host["id"]), payload)
    console.print("[green]Deleted[/green]")


@location_advanced_app.command("get")
def location_advanced_get(identifier: str, path: str):
    _, client = make_client()
    host = resolve_proxy(client.list_proxy_hosts(), identifier)
    full = client.get_proxy_host(int(host["id"]))
    loc = next((x for x in full.get("locations") or [] if x.get("path") == path), None)
    if loc is None:
        raise typer.BadParameter(f"Location not found: {path}")
    sys.stdout.write(loc.get("advanced_config") or "")


@location_advanced_app.command("set")
def location_advanced_set(
    identifier: str,
    path: str,
    value: str = typer.Option(None, "--value", "--advanced"),
    file: Path = typer.Option(None, "--file", "-f"),
    stdin_flag: bool = typer.Option(False, "--stdin"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    output: str = typer.Option("yaml", "--output", "-o"),
):
    _, client = make_client()
    snippet = read_snippet(value, file, stdin_flag)
    if snippet is None:
        raise typer.BadParameter("Provide --value, --file, or --stdin")
    result = set_location_advanced(client, identifier, path, snippet, dry_run=dry_run)
    dump(result, output)


@location_advanced_app.command("clear")
def location_advanced_clear(identifier: str, path: str):
    _, client = make_client()
    set_location_advanced(client, identifier, path, "")
    console.print("[green]Cleared[/green]")
