import json

from npmctl.config import Config


def test_migrates_single_profile_config(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({"url": "https://npm.example.com", "token": "t", "identity": "u", "verify_tls": False}))
    monkeypatch.setenv("NPMCTL_CONFIG", str(cfg_path))
    cfg = Config.load()
    assert cfg.current_profile == "default"
    assert cfg.url == "https://npm.example.com"
    assert cfg.token == "t"
    assert cfg.identity == "u"
    assert cfg.verify_tls is False


def test_profiles_save_and_switch(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    monkeypatch.setenv("NPMCTL_CONFIG", str(cfg_path))
    cfg = Config.load()
    cfg.add_profile("home", url="nginx.ntwc.top", use=True)
    cfg.identity = "a@example.com"
    cfg.password = "secret"
    cfg.save()

    loaded = Config.load()
    assert loaded.current_profile == "home"
    assert loaded.url == "https://nginx.ntwc.top"
    assert loaded.identity == "a@example.com"
    assert loaded.password == "secret"
    assert loaded.display()["has_password"] is True
