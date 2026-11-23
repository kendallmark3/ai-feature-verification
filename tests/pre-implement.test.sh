#!/usr/bin/env bash
# Tests for hooks/pre-implement.sh. Run from anywhere: bash tests/pre-implement.test.sh
set -uo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
hook="$root/hooks/pre-implement.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
failures=0

expect() {
  local want="$1" label="$2" file="$3" got=0
  bash "$hook" "$file" >"$tmp/out" 2>&1 || got=$?
  if [ "$want" = pass ] && [ "$got" -eq 0 ]; then echo "ok   - $label"
  elif [ "$want" = fail ] && [ "$got" -ne 0 ]; then echo "ok   - $label"
  else echo "FAIL - $label (exit $got)"; sed 's/^/       /' "$tmp/out"; failures=$((failures + 1))
  fi
}

expect pass "this repo's filled current-feature.md is sufficient" "$root/intent/current-feature.md"
expect fail "blank feature template is not sufficient" "$root/templates/feature-template.md"
expect fail "missing file fails" "$tmp/does-not-exist.md"

cat >"$tmp/new.md" <<'EOF'
# Current Feature

## Outcome
Operators can see failed jobs at a glance.

## Success / Evidence
A failed job is visible on the dashboard without scrolling.
EOF
expect pass "outcome and evidence alone are sufficient" "$tmp/new.md"

cat >"$tmp/old.md" <<'EOF'
# Current Feature
Business Outcome
Operators can see failed jobs at a glance.
Requirements
Constraints
Acceptance Criteria
A failed job is visible on the dashboard without scrolling.
EOF
expect pass "previous format is still accepted" "$tmp/old.md"

cat >"$tmp/no-evidence.md" <<'EOF'
# Current Feature

## Outcome
Operators can see failed jobs at a glance.

## Success / Evidence

## Constraints / Boundaries
Do not change the backend.
EOF
expect fail "outcome without evidence is not sufficient" "$tmp/no-evidence.md"
if grep -q "Success / Evidence" "$tmp/out" && ! grep -q -- "- Outcome" "$tmp/out"; then
  echo "ok   - names only the missing section"
else
  echo "FAIL - names only the missing section"; failures=$((failures + 1))
fi

cat >"$tmp/comments.md" <<'EOF'
# Current Feature

## Outcome
<!-- What should be true when this is done? -->

## Success / Evidence
<!-- How will we know? -->
EOF
expect fail "guidance comments do not count as content" "$tmp/comments.md"

cat >"$tmp/delta.md" <<'EOF'
# Current Feature

## Outcome
Operators can see failed jobs at a glance.

## Success / Evidence
A failed job is visible on the dashboard without scrolling.

# Intent Delta

## Observation
The dashboard feels too busy.

## Change
Make failures obvious.
EOF
expect pass "an appended delta keeps the intent sufficient" "$tmp/delta.md"

# The PreToolUse wrapper (pre-implement-hook.sh) ships with the intent-drive-starter plugin and is tested there.

if [ "$failures" -ne 0 ]; then
  echo "$failures test(s) failed"
  exit 1
fi
echo "all tests passed"
