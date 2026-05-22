import json
import secrets
from dataclasses import dataclass
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"


@dataclass
class AppConfig:
    root_path: str = ""
    secret_key: str = ""

    def __post_init__(self):
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)


def load_config() -> AppConfig:
    if SETTINGS_FILE.exists():
        data = json.loads(SETTINGS_FILE.read_text())
        cfg = AppConfig(**{k: v for k, v in data.items() if k in ['root_path', 'secret_key']})
    else:
        cfg = AppConfig()
        save_config(cfg)
    return cfg


def save_config(cfg: AppConfig) -> None:
    SETTINGS_FILE.write_text(
        json.dumps({"root_path": cfg.root_path, "secret_key": cfg.secret_key}, indent=2)
    )

