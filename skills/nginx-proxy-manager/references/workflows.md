# Workflows

## Safe proxy apply

1. Understand desired domain and target URL.
2. Run `npmctl proxy get DOMAIN -o json` if the host may already exist.
3. Run `npmctl proxy apply DOMAIN --to URL ...`.
4. If the user provided a host-level snippet, set it with `npmctl proxy advanced set`.
5. If the user provided a per-path snippet, create/update the custom location then set `location advanced`.
6. Verify with `npmctl proxy get DOMAIN -o json` and `npmctl proxy test DOMAIN` when public.

## Root redirect pattern

Use host-level advanced config, not a target path in `forward_host`:

```nginx
if ($request_uri = "/") {
    return 302 /management.html;
}
```

## Location updates

For path-specific upstreams or snippets, use `npmctl proxy location apply`. Do not manually put full `location {}` blocks into host-level advanced config unless the user explicitly wants raw Nginx and understands possible conflicts with NPM-generated locations.

## Certificate matching

Use `--cert auto` for normal homelab domains. If no match is found, ask the user for `--cert CERT_ID` or whether to continue without SSL.
