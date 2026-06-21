import json
import os
from pathlib import Path

_BASE = Path(__file__).parent.parent
_CONFIG = _BASE / "config.json"
_DEFAULT = _BASE / "config.example.json"


def load_config() -> dict:
    path = _CONFIG if _CONFIG.exists() else _DEFAULT
    cfg = json.loads(path.read_text())
    if key := os.environ.get("ANTHROPIC_API_KEY"):
        cfg["anthropic_api_key"] = key
    return cfg


def save_config(cfg: dict) -> None:
    _CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
