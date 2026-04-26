from npmctl.services import apply_proxy, sanitize_proxy_payload, set_host_advanced


class FakeClient:
    def __init__(self):
        self.updated = None
        self.created = None
        self.host = {
            "id": 64,
            "domain_names": ["cpa.ntwc.top"],
            "forward_scheme": "http",
            "forward_host": "old",
            "forward_port": 80,
            "certificate_id": 12,
            "ssl_forced": True,
            "allow_websocket_upgrade": True,
            "http2_support": True,
            "advanced_config": "keep-me",
            "locations": [{"id": 1, "path": "/api", "forward_scheme": "http", "forward_host": "api", "forward_port": 8080, "advanced_config": "loc"}],
            "owner": {"read_only": True},
        }

    def list_proxy_hosts(self):
        return [self.host]

    def get_proxy_host(self, host_id):
        assert host_id == 64
        return dict(self.host)

    def update_proxy_host(self, host_id, payload):
        self.updated = payload
        return {"id": host_id, **payload}

    def create_proxy_host(self, payload):
        self.created = payload
        return {"id": 99, **payload}

    def list_certificates(self):
        return [{"id": 12, "domain_names": ["*.ntwc.top"]}]


def test_sanitize_drops_readonly_and_preserves_locations():
    payload = sanitize_proxy_payload(FakeClient().host)
    assert "owner" not in payload
    assert payload["locations"][0]["id"] == 1
    assert payload["locations"][0]["advanced_config"] == "loc"


def test_apply_proxy_preserves_advanced_when_unspecified():
    client = FakeClient()
    action, result = apply_proxy(client, "cpa.ntwc.top", "http://192.168.35.100:8317", cert="auto")
    assert action == "updated"
    assert client.updated["forward_host"] == "192.168.35.100"
    assert client.updated["advanced_config"] == "keep-me"
    assert client.updated["locations"][0]["advanced_config"] == "loc"


def test_set_host_advanced_overwrites_only_host_snippet():
    client = FakeClient()
    result = set_host_advanced(client, "cpa.ntwc.top", "new")
    assert client.updated["advanced_config"] == "new"
    assert client.updated["locations"][0]["advanced_config"] == "loc"
