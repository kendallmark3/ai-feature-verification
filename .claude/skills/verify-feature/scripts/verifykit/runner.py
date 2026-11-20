"""Execute the repository's own test suites. Deterministic, no shell, no installs.

Each suite in verify.config.json names a command the team already uses
(npm, pytest, mvn, gradle, go, dotnet ...) and where its JUnit XML lands.
The runner clears stale reports, runs the command, streams the log, and copies
reports and artifacts into verification/<KEY>/runs/<run-id>/ as evidence.

A suite that breaks a guardrail is BLOCKED (not run, reason recorded); one whose
tool is missing is NOT STARTED. Neither stops the other suites, and neither is
ever counted as passing. Pipeline mode withholds unpromoted test files for the
run and restores them afterwards, even if the run fails.
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
from .inspect_repo import PROPOSED
from .util import (VerifyError, expand_env, git_changes, git_sha, git_show_head, now_iso, out_dir, read_json,
                   redact, rel, write_json)


def _expand_globs(base: Path, patterns: list[str]) -> list[Path]:
    hits: list[Path] = []
    for pat in patterns:
        hits += [Path(p) for p in sorted(glob.glob(str(base / pat), recursive=True)) if Path(p).is_file()]
    return hits


def _under(path: str, prefixes: list[str]) -> bool:
    return any(path == p.rstrip("/") or path.startswith(p.rstrip("/") + "/") for p in prefixes if p)


def working_tree(cfg: dict, test_paths: list[str]) -> dict:
    """What differs from the commit the evidence will be attributed to.

    protected_source_changed: application code listed in guardrails.protected_paths.
    committed_tests_changed: reviewed tests (no @ai-proposed marker at HEAD) edited or deleted.
    The verification output folder is ignored: the engine writes there itself.
    """
    root = Path(cfg["_root"])
    changes = git_changes(root)
    if changes is None:
        return {"clean": None, "note": "git not available; source revision unknown"}
    out_base = cfg.get("output_dir", "verification")
    changes = [c for c in changes if not _under(c["path"], [out_base])]
    protected = cfg.get("guardrails", {}).get("protected_paths", [])
    committed_tests = []
    for c in changes:
        if c["status"] != "??" and _under(c["path"], test_paths):
            head = git_show_head(root, c["path"])
            if head is not None and not PROPOSED.search(head):
                committed_tests.append(c["path"])
    return {
        "clean": not changes,
        "changed": [c["path"] for c in changes][:200],
        "protected_source_changed": [c["path"] for c in changes if _under(c["path"], protected)],
        "committed_tests_changed": committed_tests,
    }


def _withhold(root: Path, run_dir: Path, files: list[str]) -> None:
    """Move unpromoted test files out of the suites for a pipeline run. Always restored afterwards."""
    record = {"files": files, "restored": False, "at": now_iso()}
    write_json(run_dir / "withheld.json", record)
    for f in files:
        dst = run_dir / "withheld" / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root / f), str(dst))


def restore_withheld(root: Path, run_dir: Path) -> list[str]:
    """Put withheld files back. Never overwrites: if the original path is taken, the copy stays and is reported."""
    rec_path = run_dir / "withheld.json"
    if not rec_path.is_file():
        return []
    rec = read_json(rec_path)
    problems = []
    for f in rec.get("files", []):
        src, dst = run_dir / "withheld" / f, root / f
        if not src.exists():
            continue
        if dst.exists():
            problems.append(f"{f}: a file now exists at that path; the withheld copy is kept at {rel(src, root)}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    rec["restored"] = not problems
    rec["restore_problems"] = problems
    write_json(rec_path, rec)
    return problems


def _recover(cfg: dict, key: str) -> None:
    """If an earlier pipeline run was killed before restoring withheld files, restore them first."""
    root = Path(cfg["_root"])
    for rec in sorted((out_dir(cfg, key) / "runs").glob("*/withheld.json")):
        if not read_json(rec).get("restored"):
            problems = restore_withheld(root, rec.parent)
            print(f"[verify] restored test files withheld by interrupted run {rec.parent.name}"
                  + (f"; problems: {problems}" if problems else ""), flush=True)


def run(cfg: dict, key: str, suites: list[str] | None, mode: str, env_name: str) -> dict:
    root = Path(cfg["_root"])
    rails = cfg.get("guardrails", {})
    allowed = rails.get("allowed_commands", ["npm", "npx", "node", "pytest", "python3", "mvn", "gradle", "go", "dotnet"])
    deny = rails.get("deny_url_patterns", [])
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
    env_cfg = envs[env_name]
    target_env = {k: str(v) for k, v in expand_env(env_cfg).items() if not isinstance(v, (bool, dict, list))}
    # A production environment refuses the whole run: every suite would target it.
    g.check_target(target_env, deny)

    _recover(cfg, key)
    test_paths = [p for n in names for p in all_suites[n].get("test_paths", [])]
    unpromoted = g.unapproved_tests(root, test_paths)

    run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out_dir(cfg, key) / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id, "story": key, "mode": mode, "environment": env_name,
        "target": {k: v for k, v in target_env.items() if not g.SECRET_KEY.search(k)},
        "git_sha": git_sha(root), "working_tree": working_tree(cfg, test_paths),
        "started": now_iso(), "suites": [],
        # Interactive runs execute unpromoted tests (labelled); pipeline runs withhold them.
        "unpromoted": {"policy": "withheld" if mode == "pipeline" else "executed-unpromoted", "files": unpromoted},
    }

    withheld = mode == "pipeline" and bool(unpromoted)
    if withheld:
        _withhold(root, run_dir, unpromoted)
        print(f"[verify] pipeline mode: withheld {len(unpromoted)} unpromoted test file(s) (Gate 2 open):", flush=True)
        for f in unpromoted:
            print(f"  - {f}", flush=True)
    try:
        for name in names:
            manifest["suites"].append(_run_suite(cfg, name, all_suites[name], env_name, env_cfg, target_env,
                                                 mode, run_dir, allowed, deny, timeout, unpromoted))
    finally:
        if withheld:
            problems = restore_withheld(root, run_dir)
            manifest["unpromoted"]["restore_problems"] = problems
            if problems:
                print(f"[verify] WARNING could not restore: {problems}", flush=True)

    manifest["finished"] = now_iso()
    write_json(run_dir / "run.json", manifest)
    latest = out_dir(cfg, key) / "runs" / "LATEST"
    latest.write_text(run_id + "\n", encoding="utf-8")
    return manifest


def _run_suite(cfg, name, s, env_name, env_cfg, target_env, mode, run_dir, allowed, deny, timeout, unpromoted) -> dict:
    root = Path(cfg["_root"])
    cwd = (root / s.get("cwd", ".")).resolve()
    suite_env = {**target_env, **{k: str(v) for k, v in expand_env(s.get("env", {})).items()}}
    in_suite = [f for f in unpromoted if _under(f, s.get("test_paths", []))]
    entry = {
        "name": name, "framework": s.get("framework", ""), "command": s.get("command", ""),
        "cwd": rel(cwd, root), "status": "ran", "reason": "", "exit_code": None, "duration_s": 0,
        "log": "", "junit": [], "artifacts": [], "report_base": rel(cwd / s.get("report_base", "."), root),
        "unpromoted": in_suite if mode != "pipeline" else [],
        "withheld": in_suite if mode == "pipeline" else [],
        "env": {k: v for k, v in suite_env.items() if not g.SECRET_KEY.search(k)},
    }

    reason = g.suite_violation(s, suite_env, env_cfg, env_name, allowed, deny)
    if reason:
        entry.update(status="blocked", reason=reason)
        print(f"\n⊘ [{name}] BLOCKED, not run: {reason}", flush=True)
        return entry
    argv = g.parse_command(s["command"], allowed)
    exe = shutil.which(argv[0], path=os.environ.get("PATH"))
    if not cwd.is_dir() or exe is None:
        why = f"working directory {rel(cwd, root)} does not exist" if not cwd.is_dir() \
            else f"'{argv[0]}' is not installed or not on PATH"
        entry.update(status="not-started", reason=why)
        print(f"\n⊘ [{name}] could not start: {why}", flush=True)
        return entry

    for stale in _expand_globs(cwd, s.get("junit", [])):
        stale.unlink()
    env = {**os.environ, **suite_env, "CI": "1"}
    log_path = run_dir / f"{name}.log"
    print(f"\n▶ [{name}] {s['command']}  (cwd={rel(cwd, root)}, env={env_name}, mode={mode})", flush=True)
    t0 = time.monotonic()
    exit_code: int | None
    with open(log_path, "w", encoding="utf-8") as log:
        try:
            proc = subprocess.Popen([exe, *argv[1:]], cwd=cwd, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                    text=True, encoding="utf-8", errors="replace")
        except OSError as e:
            entry.update(status="not-started", reason=f"could not start '{argv[0]}': {e}")
            print(f"⊘ [{name}] could not start: {e}", flush=True)
            return entry
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                log.write(redact(line))
                sys.stdout.write(line)
            exit_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            exit_code = None
            log.write(f"\n[verify] killed after {timeout}s (guardrails.max_runtime_seconds)\n")
    duration = round(time.monotonic() - t0, 2)

    dest = run_dir / name
    for f in _expand_globs(cwd, s.get("junit", [])):
        target = dest / "junit" / f.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        entry["junit"].append(rel(target, root))
    for f in _expand_globs(cwd, s.get("artifacts", [])):
        target = dest / "artifacts" / f.relative_to(cwd)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        entry["artifacts"].append(rel(target, root))
    entry.update(exit_code=exit_code, duration_s=duration, log=rel(log_path, root))
    status = "timeout" if exit_code is None else ("ok" if exit_code == 0 else f"exit {exit_code}")
    print(f"◀ [{name}] {status} in {duration}s · {len(entry['junit'])} report(s), {len(entry['artifacts'])} artifact(s)")
    return entry


def latest_run(cfg: dict, key: str, run_id: str | None = None) -> Path:
    runs = out_dir(cfg, key) / "runs"
    rid = run_id or ((runs / "LATEST").read_text().strip() if (runs / "LATEST").is_file() else "")
    if not rid or not (runs / rid / "run.json").is_file():
        raise VerifyError(f"No run found for {key}. Run: verify.py run {key}")
    return runs / rid
