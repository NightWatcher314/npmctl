# npmctl

`npmctl` is a Python CLI for automating [Nginx Proxy Manager](https://nginxproxymanager.com/) through its API.

It focuses on safe Proxy Host workflows: creating and updating hosts without clobbering unspecified fields, matching existing certificates, managing raw `advanced_config` snippets, and configuring custom locations.

## Install

With Homebrew:

```bash
brew tap NightWatcher314/homebrew-formula
brew install npmctl
```

For development:

```bash
uv sync
uv run npmctl --help
```

## Configure

Create a profile and log in:

```bash
npmctl config profile add home --url https://nginx.example.com --use
npmctl auth login --identity admin@example.com
npmctl auth status
```

Use a specific profile for one command:

```bash
NPMCTL_PROFILE=home npmctl proxy list
```

Inspect the active configuration:

```bash
npmctl config get
npmctl doctor
```

## Proxy Hosts

List and inspect Proxy Hosts:

```bash
npmctl proxy list
npmctl proxy get app.example.com -o json
```

Create or update a host:

```bash
npmctl proxy apply app.example.com \
  --to http://192.168.1.10:8080 \
  --cert auto \
  --force-ssl \
  --websocket \
  --http2
```

`proxy apply` preserves existing fields that are not specified on the command line. This is intended to make repeated automation safe.

Test a public host:

```bash
npmctl proxy test app.example.com
```

## Certificates

List certificates and find the best match for a domain:

```bash
npmctl cert list -o json
npmctl cert match app.example.com -o json
```

## Advanced Config

Set host-level `advanced_config` from stdin:

```bash
npmctl proxy advanced set app.example.com --stdin <<'NGINX'
if ($request_uri = "/") {
    return 302 /management.html;
}
NGINX
```

Set a custom location and its location-level `advanced_config`:

```bash
npmctl proxy location apply app.example.com /api --to http://192.168.1.10:8081
npmctl proxy location advanced set app.example.com /api --stdin <<'NGINX'
proxy_set_header X-Forwarded-Prefix /api;
NGINX
```

Targets must be origin URLs such as `http://host:port`. Do not put URL paths in `forward_host`; use custom locations, `forward_path`, or Nginx snippets for path behavior.

## Authentication and Storage

By default, `npmctl` saves API tokens but not passwords. To save a password in the active profile:

```bash
NPMCTL_PASSWORD='...' npmctl auth login --identity admin@example.com --save-password
```

Later logins can reuse the saved password:

```bash
npmctl auth login --use-saved-password
```

The config file is stored at `~/.config/npmctl/config.json` with mode `0600`, but saved passwords are still plaintext. Only use `--save-password` on machines you trust.

## License

MIT
