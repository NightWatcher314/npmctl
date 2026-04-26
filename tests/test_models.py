import pytest

from npmctl.models import parse_target, wildcard_matches
from npmctl.errors import ConfigError


def test_parse_target_defaults_port():
    t = parse_target("http://192.168.35.100:8317")
    assert (t.scheme, t.host, t.port, t.path) == ("http", "192.168.35.100", 8317, "")


def test_parse_target_path_is_preserved_for_location_forward_path():
    t = parse_target("https://example.com/app")
    assert (t.scheme, t.host, t.port, t.path) == ("https", "example.com", 443, "/app")


def test_parse_target_rejects_missing_scheme():
    with pytest.raises(ConfigError):
        parse_target("192.168.35.100:8317")


def test_wildcard_matches_single_label_only():
    assert wildcard_matches("*.ntwc.top", "cpa.ntwc.top")
    assert not wildcard_matches("*.ntwc.top", "deep.cpa.ntwc.top")
    assert wildcard_matches("ntwc.top", "ntwc.top")
