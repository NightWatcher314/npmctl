# npmctl command reference

```bash
npmctl config set-url URL
npmctl config profile add NAME --url URL --use
npmctl config profile list
npmctl config profile use NAME
npmctl auth login --identity EMAIL [--save-password]
npmctl auth status
npmctl doctor
```

```bash
npmctl cert list [-o table|json|yaml]
npmctl cert match DOMAIN [-o table|json|yaml]
```

```bash
npmctl proxy list [-o table|json|yaml]
npmctl proxy get DOMAIN_OR_ID [-o json|yaml]
npmctl proxy apply DOMAIN --to URL [--cert auto|none|ID] [--force-ssl/--no-force-ssl] [--websocket/--no-websocket] [--http2/--no-http2] [--advanced-file FILE|--advanced-stdin|--advanced TEXT|--clear-advanced] [--dry-run]
npmctl proxy delete DOMAIN_OR_ID --yes
npmctl proxy enable DOMAIN_OR_ID
npmctl proxy disable DOMAIN_OR_ID
npmctl proxy test DOMAIN [--path PATH]
```

```bash
npmctl proxy advanced get DOMAIN_OR_ID
npmctl proxy advanced set DOMAIN_OR_ID --file FILE
npmctl proxy advanced set DOMAIN_OR_ID --stdin
npmctl proxy advanced clear DOMAIN_OR_ID
```

```bash
npmctl proxy location list DOMAIN_OR_ID [-o json|yaml]
npmctl proxy location apply DOMAIN_OR_ID PATH --to URL [--advanced-file FILE|--advanced-stdin|--advanced TEXT] [--dry-run]
npmctl proxy location delete DOMAIN_OR_ID PATH --yes
npmctl proxy location advanced get DOMAIN_OR_ID PATH
npmctl proxy location advanced set DOMAIN_OR_ID PATH --file FILE
npmctl proxy location advanced set DOMAIN_OR_ID PATH --stdin
npmctl proxy location advanced clear DOMAIN_OR_ID PATH
```
