from __future__ import annotations

import json
import sys
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

console = Console()


def dump(data: Any, output: str = "table", table: Table | None = None) -> None:
    if output == "json":
        console.print_json(json.dumps(data, ensure_ascii=False))
    elif output == "yaml":
        sys.stdout.write(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    elif table is not None:
        console.print(table)
    else:
        console.print(data)
