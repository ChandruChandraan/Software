"""Backend configuration settings supporting environment variables and config files."""

import json
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "firing_sim.db"


class BackendConfig(BaseModel):
    """Configuration model for Firing Simulator Backend."""
    app_name: str = "FiringSimulator-Backend"
    version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str = f"sqlite:///{DEFAULT_DB_PATH}"
    udp_listen_host: str = "127.0.0.1"
    udp_listen_port: int = 47001
    tracker_stale_threshold_seconds: float = 5.0
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    secret_key: str = "simulator-dev-secret-key"
    log_level: str = "INFO"
    log_format: str = "structured"  # "structured" or "json"


def _parse_env_list(val: str) -> List[str]:
    """Parse comma-separated string into list of stripped strings."""
    return [item.strip() for item in val.split(",") if item.strip()]


def load_config(config_file: Optional[str | Path] = None) -> BackendConfig:
    """
    Load configuration with precedence:
    1. Environment variables
    2. Configuration file (JSON)
    3. Defaults
    """
    config_dict = {}

    # 1. Attempt loading from config file if provided or if default config.json exists
    if config_file is None:
        env_config = os.getenv("SIM_CONFIG_PATH")
        if env_config:
            config_file = Path(env_config)
        else:
            default_cfg = BASE_DIR / "config.json"
            if default_cfg.exists():
                config_file = default_cfg

    if config_file and Path(config_file).exists():
        with open(config_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            if isinstance(file_data, dict):
                config_dict.update(file_data)

    # 2. Override with Environment variables
    env_mappings = {
        "SIM_BACKEND_HOST": ("host", str),
        "SIM_BACKEND_PORT": ("port", int),
        "SIM_DATABASE_URL": ("database_url", str),
        "SIM_UDP_LISTEN_HOST": ("udp_listen_host", str),
        "SIM_UDP_LISTEN_PORT": ("udp_listen_port", int),
        "SIM_SECRET_KEY": ("secret_key", str),
        "SIM_LOG_LEVEL": ("log_level", str),
        "SIM_LOG_FORMAT": ("log_format", str),
        "SIM_TRACKER_STALE_THRESHOLD": ("tracker_stale_threshold_seconds", float),
    }

    for env_var, (field_name, field_type) in env_mappings.items():
        val = os.getenv(env_var)
        if val is not None:
            if field_type == int:
                try:
                    config_dict[field_name] = int(val)
                except ValueError:
                    pass
            elif field_type == float:
                try:
                    config_dict[field_name] = float(val)
                except ValueError:
                    pass
            elif field_type == bool:
                config_dict[field_name] = val.lower() in ("true", "1", "yes")
            else:
                config_dict[field_name] = val

    cors_val = os.getenv("SIM_CORS_ORIGINS")
    if cors_val:
        config_dict["cors_origins"] = _parse_env_list(cors_val)

    return BackendConfig(**config_dict)


_config_instance: Optional[BackendConfig] = None


def get_config() -> BackendConfig:
    """Retrieve global cached backend configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


def reset_config(new_config: Optional[BackendConfig] = None) -> BackendConfig:
    """Reset configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = new_config
    return get_config()
