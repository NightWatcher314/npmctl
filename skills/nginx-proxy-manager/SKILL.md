---
name: nginx-proxy-manager
description: Use when managing Nginx Proxy Manager via the local npmctl CLI, including proxy hosts, certificates, host-level advanced_config snippets, custom locations, and per-location advanced_config snippets.
metadata:
  short-description: Manage Nginx Proxy Manager with npmctl
---

# Nginx Proxy Manager via npmctl

Use `npmctl` as the stable executor for Nginx Proxy Manager changes. Prefer it over raw API calls unless a required operation is not supported.

## Core rules

- Never put URL paths in `forward_host`; targets are `http://host:port`. Use custom locations, `forward_path`, or `advanced_config` for path behavior.
- Host-level snippets go in proxy host `advanced_config` via `npmctl proxy advanced ...`.
- Per-location snippets go in `locations[].advanced_config` via `npmctl proxy location advanced ...`.
- For updates, preserve unspecified fields, existing `advanced_config`, and existing `locations` unless the user explicitly asks to clear/replace them. `npmctl proxy apply` is designed to do this.
- After mutations, verify with `npmctl proxy get DOMAIN -o json`; if public, also run `npmctl proxy test DOMAIN`.
- Destructive actions such as delete, clear advanced config, or removing locations should be explicit in the user request.

## Common commands

Configure profiles and login:

```bash
npmctl config profile add home --url https://nginx.ntwc.top --use
npmctl auth login --identity USER_EMAIL
npmctl auth status
```

Use `NPMCTL_PROFILE=name` for one-off commands. Passwords may be saved with `npmctl auth login --save-password`, but this stores plaintext in the local config file; only do it when the user explicitly wants that.

Inspect:

```bash
npmctl doctor
npmctl cert list -o json
npmctl cert match app.ntwc.top -o json
npmctl proxy list
npmctl proxy get app.ntwc.top -o json
```

Create/update a proxy host safely:

```bash
npmctl proxy apply app.ntwc.top \
  --to http://192.168.35.100:8080 \
  --cert auto \
  --force-ssl \
  --websocket \
  --http2
```

Set a host-level advanced snippet from a file:

```bash
npmctl proxy advanced set app.ntwc.top --file /tmp/advanced.conf
```

Set a host-level advanced snippet from stdin:

```bash
npmctl proxy advanced set app.ntwc.top --stdin <<'NGINX'
if ($request_uri = "/") {
    return 302 /management.html;
}
NGINX
```

Manage a custom location:

```bash
npmctl proxy location apply app.ntwc.top /api --to http://192.168.35.100:8081
npmctl proxy location advanced set app.ntwc.top /api --file /tmp/api-location.conf
```

## When details are needed

- For task workflows and safety checks, read `references/workflows.md`.
- For supported command shapes, read `references/commands.md`.
