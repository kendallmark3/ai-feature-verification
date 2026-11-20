"""Shared helpers: config loading, paths, JSON IO. Standard library only."""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
from pathlib import Path

CONFIG_NAME = "verify.config.json"
_ENV_REF = re.compile(r"\$\{([A-Z0-9_]+)\}")


class VerifyError(Exception):
    """A user-facing error. The CLI prints the message and exits non-zero."""


def repo_root() -> Path:
    """The directory holding verify.config.json, searching upward from cwd."""
    here = Path.cwd().resolve()
    for d in (here, *here.parents):
        if (d / CONFIG_NAME).is_file():
            return d
    raise VerifyError(
        f"{CONFIG_NAME} not found in {here} or any parent. "
        "Run `verify.py init` to create one, then edit it."
    )


def expand_env(value):
    """Replace ${VAR} references with environment values (missing -> empty)."""
    if isinstance(value, str):
        return _ENV_REF.sub(lambda m: os.environ.get(m.group(1), ""), value)
    if isinstance(value, list):
        return [expand_env(v) for v in value]
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    return value


def load_config(root: Path | None = None) -> dict:
    root = root or repo_root()
    path = root / CONFIG_NAME
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise VerifyError(f"{path} is not valid JSON: {e}") from e
    cfg["_root"] = str(root)
    return cfg


def out_dir(cfg: dict, key: str) -> Path:
    base = Path(cfg["_root"]) / cfg.get("output_dir", "verification")
    d = base / key
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(path: Path, default=None):
    if not path.is_file():
        if default is not None:
            return default
        raise VerifyError(f"Missing {path}. Run the earlier step first.")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today() -> str:
    return _dt.date.today().isoformat()


def git_sha(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def rel(path: Path, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)
