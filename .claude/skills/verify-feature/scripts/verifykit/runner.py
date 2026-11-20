"""Execute the repository's own test suites. Deterministic, no shell, no installs.

Each suite in verify.config.json names a command the team already uses
(npm, pytest, mvn, gradle, go, dotnet ...) and where its JUnit XML lands.
The runner clears stale reports, runs the command, streams the log, and copies
reports and artifacts into verification/<KEY>/runs/<run-id>/ as evidence.
"""
from __future__ import annotations

import datetime as _dt
import glob
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import guardrails as g
from .util import VerifyError, expand_env, git_sha, now_iso, out_dir, rel, write_json


def _expand_globs(base: Path, patterns: list[str]) -> list[Path]:
    hits: list[Path] = []
    for pat in patterns:
        hits += [Path(p) for p in sorted(glob.glob(str(base / pat), recursive=True)) if Path(p).is_file()]
    return hits


def run(cfg: dict, key: str, suites: list[str] | None, mode: str, env_name: str) -> dict:
    root = Path(cfg["_root"])
    rails = cfg.get("guardrails", {})
    allowed = rails.get("allowed_commands", ["npm", "npx", "node", "pytest", "python3", "mvn", "gradle", "go", "dotnet"])
    timeout = int(rails.get("max_runtime_seconds", 900))
    g.check_no_literal_secrets({k: v for k, v in cfg.items() if not k.startswith("_")})

    all_suites = cfg.get("suites", {})
    names = suites or list(all_suites)
    unknown = [n for n in names if n not in all_suites]
    if unknown:
        raise VerifyError(f"Unknown suite(s) {unknown}. Configured: {list(all_suites)}")

    envs = cfg.get("environments", {"local": {}})
    if env_name not in envs:
        raise VerifyError(f"Unknown environment '{env_name}'. Configured: {list(envs)}")
    target_env = {k: str(v) for k, v in expand_env(envs[env_name]).items()}
    g.check_target(target_env, rails.get("deny_url_patterns", []))

    if mode == "pipeline":
        paths = [p for n in names for p in all_suites[n].get("test_paths", [])]
        pending = g.unapproved_tests(root, paths)
        if pending:
            raise VerifyError(
                "Gate 2 not passed: these tests are still marked @ai-proposed and cannot run in pipeline mode:\n  "
                + "\n  ".join(pending)
                + "\nReview them and run `verify.py promote <file> --by <name>` (a person, not Claude)."
            )

    run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out_dir(cfg, key) / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id, "story": key, "mode": mode, "environment": env_name,
        "target": {k: v for k, v in target_env.items() if not g.SECRET_KEY.search(k)},
        "git_sha": git_sha(root), "started": now_iso(), "suites": [],
    }

    for name in names:
        s = all_suites[name]
        cwd = (root / s.get("cwd", ".")).resolve()
        argv = g.parse_command(s["command"], allowed)
        exe = shutil.which(argv[0], path=os.environ.get("PATH")) or argv[0]
        for stale in _expand_globs(cwd, s.get("junit", [])):
            stale.unlink()
        env = {**os.environ, **target_env, **{k: str(v) for k, v in expand_env(s.get("env", {})).items()}, "CI": "1"}
        log_path = run_dir / f"{name}.log"
        print(f"\n▶ [{name}] {s['command']}  (cwd={rel(cwd, root)}, env={env_name}, mode={mode})", flush=True)
        t0 = time.monotonic()
        exit_code: int | None
        with open(log_path, "w", encoding="utf-8") as log:
            try:
                proc = subprocess.Popen([exe, *argv[1:]], cwd=cwd, env=env, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            except FileNotFoundError as e:
                raise VerifyError(f"Could not start '{argv[0]}': {e}. Is it installed and on PATH?") from e
            try:
                assert proc.stdout is not None
                for line in proc.stdout:
                    log.write(line)
                    sys.stdout.write(line)
                exit_code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                exit_code = None
                log.write(f"\n[verify] killed after {timeout}s (guardrails.max_runtime_seconds)\n")
        duration = round(time.monotonic() - t0, 2)

        dest = run_dir / name
        copied_junit = []
        for f in _expand_globs(cwd, s.get("junit", [])):
            target = dest / "junit" / f.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            copied_junit.append(rel(target, root))
        copied_art = []
        for f in _expand_globs(cwd, s.get("artifacts", [])):
            target = dest / "artifacts" / f.relative_to(cwd)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            copied_art.append(rel(target, root))
        manifest["suites"].append({
            "name": name, "framework": s.get("framework", ""), "command": s["command"],
            "cwd": rel(cwd, root), "exit_code": exit_code, "duration_s": duration,
            "log": rel(log_path, root), "junit": copied_junit, "artifacts": copied_art,
            "report_base": rel(cwd / s.get("report_base", "."), root),
        })
        status = "timeout" if exit_code is None else ("ok" if exit_code == 0 else f"exit {exit_code}")
        print(f"◀ [{name}] {status} in {duration}s · {len(copied_junit)} report(s), {len(copied_art)} artifact(s)")

    manifest["finished"] = now_iso()
    write_json(run_dir / "run.json", manifest)
    latest = out_dir(cfg, key) / "runs" / "LATEST"
    latest.write_text(run_id + "\n", encoding="utf-8")
    return manifest


def latest_run(cfg: dict, key: str, run_id: str | None = None) -> Path:
    runs = out_dir(cfg, key) / "runs"
    rid = run_id or ((runs / "LATEST").read_text().strip() if (runs / "LATEST").is_file() else "")
    if not rid or not (runs / rid / "run.json").is_file():
        raise VerifyError(f"No run found for {key}. Run: verify.py run {key}")
    return runs / rid
