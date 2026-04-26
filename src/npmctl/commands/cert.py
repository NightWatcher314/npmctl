from __future__ import annotations

import typer
from rich.table import Table

from npmctl.context import make_client
from npmctl.output import dump
from npmctl.services import match_certificate

app = typer.Typer(help="Certificate helpers")


@app.command("list")
def list_certs(output: str = typer.Option("table", "--output", "-o", help="table|json|yaml")):
    _, client = make_client()
    certs = client.list_certificates()
    table = Table(title="Certificates")
    for col in ["ID", "Provider", "Domains", "Expires"]:
        table.add_column(col)
    for c in certs:
        table.add_row(str(c.get("id")), str(c.get("provider")), ", ".join(c.get("domain_names", [])), str(c.get("expires_on")))
    dump(certs, output, table)


@app.command("match")
def match(domain: str, output: str = typer.Option("table", "--output", "-o", help="table|json|yaml")):
    _, client = make_client()
    cert = match_certificate(client, domain)
    dump(cert or {}, output)
