# EXPERIMENT 001 · Run 1 · IDS-3

**Verdict: STOPPED, INCOMPLETE.** Stop condition met: the story has no acceptance criteria, so
there is nothing to test the Jira integration against. No success is claimed.

Story: IDS-3 "Integrate AI Test Harness with Jira" · intentdrivenengineering.atlassian.net ·
retrieved 2026-11-21 via Atlassian MCP `getJiraIssue`.

## Outcomes

| # | Outcome | Status | Evidence |
|---|---|---|---|
| 1 | Authenticated Jira connectivity | PASSED (MCP) · BLOCKED (REST adapter) | MCP returned site 762d785d…, Jira read-write. REST adapter: workspace cannot reach atlassian.net (curl → 000) and no `JIRA_*` credentials are set; not requested in chat. |
| 2 | Retrieve the story | PASSED | IDS-3, Story, In Progress, reporter Mark Kendall. Snapshot: `jira/IDS-3.json` |
| 3 | Extract acceptance criteria | FAILED (story) | `verify.py story IDS-3` → 0 ACs. Description empty; Summary is 255 chars and ends "As a QA en" (story pasted into Summary and truncated). |
| 4 | Traceable test plan | SKIPPED | `plan --init` wrote an empty plan (0 ACs). |
| 5 | Which ACs are testable | SKIPPED | None exist. |
| 6 | Execute integration tests | SKIPPED | Stop condition; no suites run for this story. |
| 7 | Deterministic results | PASSED (Gate 1) | `gaps` → Q-1 NO_ACCEPTANCE_CRITERIA, Q-2 NO_DESCRIPTION; `gate1 --check` exit 2. Plus Q-AI-1 SUMMARY_TRUNCATED. |
| 8 | Publish summary to Jira | PENDING authorization | Comment drafted; not posted yet. |

Regression (not story evidence): engine unit tests, 53 run, 53 passed
(`python3 -m unittest discover -s tests/verifykit`).

## Findings on the harness

- **F-1 · Empty plan passes validation.** `plan IDS-3 --check` returns `ok: true` with zero
  ACs. A story with no criteria should fail the plan check, not pass it.
- **F-2 · Cloud adapter still unexercised.** It needs network access to the Jira site and
  `JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` in the environment. Run it from a machine that
  has both (your laptop) to test the REST path.
- **F-3 · MCP-to-harness handoff is manual.** The MCP result was copied into the existing local
  adapter's file shape by hand. That worked with no new code, but it is the seam a small MCP
  path would close, once the REST adapter has been tested.

## To unblock run 2
1. Move the IDS-3 story text into Description and add an "Acceptance Criteria" list (Q-1, Q-2, Q-AI-1).
2. Run the REST adapter once from a machine with credentials (F-2).
