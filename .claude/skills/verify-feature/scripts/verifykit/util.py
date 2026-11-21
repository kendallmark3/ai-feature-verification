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


def git_changes(root: Path) -> list[dict] | None:
    """Uncommitted changes as [{"path", "status"}], or None when git is unavailable."""
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                             cwd=root, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    changes = []
    for line in out.stdout.splitlines():
        if len(line) > 3:
            path = line[3:].split(" -> ")[-1].strip().strip('"')
            changes.append({"path": path, "status": line[:2].strip() or "?"})
    return changes


def git_show_head(root: Path, path: str) -> str | None:
    """The committed (HEAD) text of a file, or None if it is not in HEAD."""
    try:
        out = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


_SECRET_NAME = re.compile(r"(token|secret|password|passwd|api[_-]?key|private[_-]?key|cookie|session)", re.I)
_REDACT_PATTERNS = [
    (re.compile(r"(?i)\b(authorization|proxy-authorization|cookie|set-cookie|x-api-key)(\"?\s*[:=]\s*\"?)[^\"\r\n]+"),
     r"\1\2[REDACTED]"),
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 [REDACTED]"),
    (re.compile(r"(?i)([?&](?:access_token|token|api_?key|apikey|key|password|secret|sig)=)[^&\s\"']+"),
     r"\1[REDACTED]"),
    (re.compile(r"(?i)(\"?(?:api[_-]?key|token|secret|password|passwd|client[_-]?secret)\"?\s*[:=]\s*\"?)"
                r"(?!\$\{)[^\"\s,&}]{4,}"), r"\1[REDACTED]"),
]
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def redact(text: str, environ: dict | None = None) -> str:
    """Remove secrets from text that will be stored as evidence.

    Values of environment variables with secret-like names are removed wherever
    they appear, then common header, query and key=value shapes are masked.
    """
    if not text:
        return text
    text = _ANSI.sub("", text)
    env = os.environ if environ is None else environ
    for name, value in env.items():
        if _SECRET_NAME.search(name) and isinstance(value, str) and len(value) >= 6:
            text = text.replace(value, "[REDACTED]")
    for pat, repl in _REDACT_PATTERNS:
        text = pat.sub(repl, text)
    return text


def rel(path: Path, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


_ENGINE = Path(__file__).resolve().parents[1] / "verify.py"


def verify_cmd(root: Path | str) -> str:
    """How to call the engine from the repo root, for text written into reports.

    Inside the repo it is the relative path; installed as a plugin it lives elsewhere, so the
    plugin-root form is written instead (stable across machines, so reports stay deterministic).
    """
    try:
        return "python3 " + _ENGINE.relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return 'python3 "${CLAUDE_PLUGIN_ROOT}/skills/verify-feature/scripts/verify.py"'
