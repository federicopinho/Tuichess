from __future__ import annotations

import importlib.util
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".tuichess"
CONFIG_PATH = CONFIG_DIR / "config.json"
KEYRING_SERVICE = "tuichess"
KEYRING_USER = "lichess_token"
KEYRING_AVAILABLE = importlib.util.find_spec("keyring") is not None
if KEYRING_AVAILABLE:
    import keyring  # type: ignore


@dataclass
class Config:
    token: Optional[str] = None


def _load_keyring_token() -> Optional[str]:
    if not KEYRING_AVAILABLE:
        return None
    return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)  # type: ignore[name-defined]


def _save_keyring_token(token: Optional[str]) -> bool:
    if not KEYRING_AVAILABLE:
        return False
    if token:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token)  # type: ignore[name-defined]
    else:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)  # type: ignore[name-defined]
    return True


def load_config() -> Config:
    token = _load_keyring_token()
    if token:
        return Config(token=token)
    if not CONFIG_PATH.exists():
        return Config()
    data = json.loads(CONFIG_PATH.read_text())
    return Config(token=data.get("token"))


def save_config(config: Config) -> None:
    if _save_keyring_token(config.token):
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {"token": config.token}
    CONFIG_PATH.write_text(json.dumps(data, indent=2))
    os.chmod(CONFIG_PATH, 0o600)


def clear_config() -> None:
    if _save_keyring_token(None):
        return
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
