"""Guardrails applied before anything executes.

- Only allow-listed executables run, with no shell (no pipes, redirects, chaining).
- The target URL may not match a production pattern.
- Secrets may not be written literally into verify.config.json.
- Suites that write shared data run only where the environment allows it.
- Pipeline mode withholds test files still marked @ai-proposed (Gate 2).

The checks raise VerifyError. The runner turns a per-suite violation into a
BLOCKED suite with the reason recorded, and carries on with the other suites.
A missing permission is never read as permission.
"""
from __future__ import annotations

import re
import shlex
from pathlib import Path

from .inspect_repo import scan_tests
from .util import VerifyError

SHELL_META = re.compile(r"[|;&<>`$]|\$\(")
SECRET_KEY = re.compile(r"(token|secret|password|passwd|api[_-]?key|private[_-]?key)", re.I)
DEFAULT_DENY = [r"(^|[./-])prod([./-]|$)", r"production"]


def parse_command(command: str, allowed: list[str]) -> list[str]:
    if SHELL_META.search(command):
        raise VerifyError(f"Command uses shell syntax, which is not allowed: {command!r}")
    argv = shlex.split(command)
    if not argv:
        raise VerifyError("Empty command.")
    if argv[0] not in allowed:
        raise VerifyError(f"'{argv[0]}' is not in guardrails.allowed_commands {allowed}.")
    return argv


def check_target(env: dict, deny_patterns: list[str]) -> None:
    for name in ("BASE_URL", "API_URL", "TARGET_URL"):
        url = env.get(name, "")
        for pat in deny_patterns or DEFAULT_DENY:
            if url and re.search(pat, url, re.I):
                raise VerifyError(f"{name}={url} matches production pattern {pat!r}. Verification never runs against prod.")


def check_no_literal_secrets(obj, path="config") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            if SECRET_KEY.search(k) and isinstance(v, str) and v and not v.startswith("${"):
                raise VerifyError(f"{path}.{k} holds a literal secret. Use an environment reference like ${{MY_TOKEN}}.")
            check_no_literal_secrets(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_no_literal_secrets(v, f"{path}[{i}]")


def check_shared_writes(suite: dict, env_cfg: dict, env_name: str) -> None:
    """A suite flagged writes_shared_data runs only where the environment explicitly allows it."""
    if suite.get("writes_shared_data") and env_cfg.get("allow_shared_data_writes") is not True:
        raise VerifyError(
            f"suite writes shared data and environment '{env_name}' does not set allow_shared_data_writes: true"
        )


def suite_violation(suite: dict, suite_env: dict, env_cfg: dict, env_name: str,
                    allowed: list[str], deny_patterns: list[str]) -> str | None:
    """Every per-suite rule in one place. Returns the reason the suite is blocked, or None."""
    try:
        parse_command(suite.get("command", ""), allowed)
        check_target(suite_env, deny_patterns)
        check_shared_writes(suite, env_cfg, env_name)
    except VerifyError as e:
        return str(e)
    return None


def unapproved_tests(root: Path, test_paths: list[str]) -> list[str]:
    hits = []
    for t in scan_tests(root):
        if t["ai_proposed"] and any(t["path"] == p.rstrip("/") or t["path"].startswith(p.rstrip("/") + "/")
                                    for p in test_paths if p):
            hits.append(t["path"])
    return hits
