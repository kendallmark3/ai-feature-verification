#!/usr/bin/env bash
# Reproduce the INTENT-001 validation runs.
#
#   bash docs/validation/INTENT-001/run-validation.sh <scratch-dir> [old-engine-dir]
#
# Copies this repository to <scratch-dir>/repo and runs every scenario there, so the
# committed verification/SHOP-142 state is never touched. Evidence is written to
# docs/validation/INTENT-001/runs/<scenario>/ in THIS repository.
#
# old-engine-dir (optional) holds the pre-INTENT-001 engine, e.g. extracted with
#   git archive dc04629 .claude/skills/verify-feature/scripts | tar -x -C <old-engine-dir>
# When given, the baseline scenarios also run on it for comparison.
#
# Needs: python3, git, node 20+, demo-app/node_modules with @playwright/test and a Chromium.
set -uo pipefail

SRC="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRATCH="${1:?usage: run-validation.sh <scratch-dir> [old-engine-dir]}"
OLD="${2:-}"
OUT="$SRC/docs/validation/INTENT-001/runs"
FIX="$SRC/docs/validation/INTENT-001/fixtures"
R="$SCRATCH/repo"
V=".claude/skills/verify-feature/scripts/verify.py"
G=(git -c user.email=validation@local -c user.name=validation)

rm -rf "$R" && mkdir -p "$SCRATCH" && cp -a "$SRC" "$R"
rm -rf "$R/verification/SHOP-142/runs" "$R/docs/validation/INTENT-001/runs"
(cd "$R" && "${G[@]}" add -A >/dev/null && "${G[@]}" commit -qm "validation snapshot" >/dev/null)
SNAP="$(git -C "$R" rev-parse HEAD)"
rm -rf "$OUT" && mkdir -p "$OUT"

# Back to the snapshot: undoes scenario commits and edits; keeps node_modules.
reset() { (cd "$R" && git reset -q --hard "$SNAP" && git clean -fdq -e demo-app/node_modules); }

# Commit scenario setup so pipeline runs see a clean revision, as CI would.
commit_setup() { (cd "$R" && "${G[@]}" add -A >/dev/null && "${G[@]}" commit -qm "scenario setup: $1" >/dev/null); }

capture() {  # capture <scenario> <engine: new|old> <args...>
  local name="$1" engine="$2"; shift 2
  local d="$OUT/$name"; mkdir -p "$d"
  local cli="$V"; [ "$engine" = old ] && cli="$OLD/$V"
  local k="$R/verification/SHOP-142"
  # Remove generated outputs first, so a refused run can't show an earlier run's verdict.
  rm -f "$k"/{VERIFICATION_REPORT.md,report.json,findings.json,evidence.json} "$k/runs/LATEST"
  ( cd "$R" && CI=1 setsid python3 "$cli" "$@" </dev/null >"$d/console.txt" 2>&1 ); local code=$?
  echo "$code" > "$d/exit-code.txt"
  echo "python3 $V $*   (engine: $engine, stdin closed, no TTY, CI=1)" > "$d/command.txt"
  for f in VERIFICATION_REPORT.md report.json findings.json gate1-status.json; do
    [ -f "$k/$f" ] && cp "$k/$f" "$d/"
  done
  if [ -f "$k/runs/LATEST" ]; then
    local run; run="$(cat "$k/runs/LATEST")"
    [ -f "$k/runs/$run/run.json" ] && cp "$k/runs/$run/run.json" "$d/run.json"
  fi
  # Keep the screenshots that findings point to (small PNGs), not the whole run folder.
  if [ -f "$d/findings.json" ]; then
    python3 - "$d/findings.json" "$R" "$d" <<'PY'
import json, shutil, sys, pathlib
f, root, d = sys.argv[1:4]
for x in json.load(open(f))["findings"]:
    for s in x.get("screenshots", []):
        src = pathlib.Path(root) / s
        if src.is_file():
            dst = pathlib.Path(d) / "screenshots" / f"{src.parent.name}-{src.name}"
            dst.parent.mkdir(exist_ok=True)
            shutil.copy2(src, dst)
PY
  fi
  printf '%-34s %-4s exit %s  %s\n' "$name" "$engine" "$code" \
    "$(python3 -c "import json;print(json.load(open('$d/report.json'))['verdict'])" 2>/dev/null || echo "(no report) $(tail -1 "$d/console.txt")")"
}

reopen_q_ai_4() {  # Simulate an unanswered question on AC-2 (the real answer exists).
  python3 - "$R/verification/SHOP-142/gate1-clarifications.md" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
s = re.sub(r"(## Q-AI-4 · AC-2 · Several codes[\s\S]*?)\nAnswer:[^\n]*", r"\1\nAnswer: ", s, count=1)
open(p, "w").write(s)
PY
}

promote_sample() {  # Simulated reviewer promotes the two SHOP-142 test files (Gate 2).
  for f in demo-app/tests/api/discount.test.mjs demo-app/tests/e2e/discount.spec.js; do
    (cd "$R" && python3 "$V" promote "$f" --by "Validation reviewer (simulated)" >/dev/null)
  done
}

echo "== baseline: SHOP-142 as merged"
reset; capture 01-shop142-interactive new all SHOP-142 --mode interactive
[ -n "$OLD" ] && { reset; capture 01-shop142-interactive-old-engine old all SHOP-142 --mode interactive; }
reset; capture 02-shop142-pipeline new all SHOP-142 --mode pipeline
[ -n "$OLD" ] && { reset; capture 02-shop142-pipeline-old-engine old all SHOP-142 --mode pipeline; }

echo "== ambiguous criterion: unrelated tests keep running"
reset; reopen_q_ai_4; capture 03-ambiguous-ac2-interactive new all SHOP-142 --mode interactive

echo "== deliberate failures"
reset
cp "$FIX/deliberate-reviewed.test.mjs" "$R/demo-app/tests/api/"
cp "$FIX/deliberate-proposed.spec.js" "$R/demo-app/tests/e2e/"
capture 04-failures-interactive new all SHOP-142 --mode interactive
[ -n "$OLD" ] && capture 04-failures-interactive-old-engine old all SHOP-142 --mode interactive

echo "== pipeline after Gate 2 (sample tests promoted; deliberate proposed test stays unpromoted)"
reset
cp "$FIX/deliberate-reviewed.test.mjs" "$R/demo-app/tests/api/"
cp "$FIX/deliberate-proposed.spec.js" "$R/demo-app/tests/e2e/"
promote_sample; commit_setup "promoted + deliberate"
capture 05-failures-pipeline-promoted new all SHOP-142 --mode pipeline

echo "== the same failure while AC-2's question is open: requirement ambiguity"
reset
cp "$FIX/deliberate-reviewed.test.mjs" "$R/demo-app/tests/api/"
promote_sample; reopen_q_ai_4; commit_setup "promoted + deliberate + open question"
capture 06-failure-on-ambiguous-ac2-pipeline new all SHOP-142 --mode pipeline

echo "== clean pipeline after Gate 2 (no deliberate tests)"
reset; promote_sample; commit_setup "promoted"
capture 07-pipeline-promoted-clean new all SHOP-142 --mode pipeline

echo "== restricted operations are blocked, safe suites continue"
reset
python3 - "$R/verify.config.json" <<'PY'
import json, sys
p = sys.argv[1]; c = json.load(open(p))
c["suites"]["load"] = {"framework": "other", "cwd": "demo-app", "command": "curl -s http://127.0.0.1:4310/api/health",
                       "junit": [], "artifacts": [], "test_paths": []}
c["suites"]["smoke-prod"] = {"framework": "playwright", "cwd": "demo-app", "command": "npx playwright test",
                             "junit": ["reports/e2e-junit.xml"], "artifacts": [],
                             "env": {"BASE_URL": "https://shop.production.example.com"}, "test_paths": []}
c["suites"]["seed-shared-data"] = {"framework": "other", "cwd": "demo-app", "command": "node -e 1",
                                   "junit": [], "artifacts": [], "writes_shared_data": True, "test_paths": []}
c["environments"]["prod-mirror"] = {"BASE_URL": "https://prod.shop.example.com"}
open(p, "w").write(json.dumps(c, indent=2))
PY
capture 08-restricted-dev new all SHOP-142 --mode interactive --env dev
capture 09-production-environment-refused new run SHOP-142 --env prod-mirror

echo "Evidence: $OUT"
