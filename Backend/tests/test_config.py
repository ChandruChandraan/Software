import os
from app.config import load_config, BackendConfig


def test_default_config():
    cfg = load_config()
    assert cfg.app_name == "FiringSimulator-Backend"
    assert cfg.port == 8000
    assert cfg.udp_listen_port == 47001
    assert "sqlite:///" in cfg.database_url


def test_env_var_override(monkeypatch):
    monkeypatch.setenv("SIM_BACKEND_PORT", "9090")
    monkeypatch.setenv("SIM_UDP_LISTEN_PORT", "48001")
    monkeypatch.setenv("SIM_LOG_LEVEL", "DEBUG")

    cfg = load_config()
    assert cfg.port == 9090
    assert cfg.udp_listen_port == 48001
    assert cfg.log_level == "DEBUG"
