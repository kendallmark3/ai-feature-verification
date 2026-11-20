# What runs automatically, gates, and verdicts

Verification runs end to end without asking for approval. People are asked only for decisions
that need their authority, and those are recorded as exceptions rather than prompts.

## Runs automatically (no approval)

Reading the story, inspecting code and tests, writing the plan, writing new test files
(marked `@ai-proposed`), running the configured suites, running unpromoted tests in
interactive mode, collecting logs, JUnit, screenshots and traces, and writing the report,
findings and evidence.

## Needs a person (never assumed)

| Decision | Recorded as | Who acts | Command / place |
|---|---|---|---|
| What an ambiguous criterion means (Gate 1) | open question, AC shown UNRESOLVED | Story owner (named on each question) | `Answer:` lines in `gate1-clarifications.md` |
| Promoting a generated test into the regression suite (Gate 2) | file still `@ai-proposed`; withheld from pipeline | Reviewer, usually via a test-only PR | `verify.py promote <file> --by <name>` |
| Accepting the story or its risks (Gate 3) | `pending human decision` | The accountable person | `verify.py approve <KEY> --by <name> --decision ...` |
| Running something a guardrail blocks | suite BLOCKED with the reason | Whoever owns `verify.config.json`, through review | config change |
| Production, shared-data writes outside permitted environments, product-code changes | refused or blocked, never automatic | A person, outside this tool | — |

Claude prepares each of these and stops there. It runs `promote` or `approve` only when a
person tells it to in the conversation, naming themselves and the decision.

`gate1 --check` exits 0 when every question is answered and 2 while any are open. Open
questions do not stop planning or testing; they leave only their own criteria UNRESOLVED.

## Criterion statuses

| Status | Meaning |
|---|---|
| PASS | Tagged tests ran in every planned suite and all passed. No open question on this AC. |
| FAIL | A tagged test ran and failed. |
| UNRESOLVED | An open Gate 1 question names this AC. Its tests may have run; it is never shown as passing until answered. |
| BLOCKED | A planned suite did not run (guardrail, missing tool), or its tests were withheld from a pipeline run because they are unpromoted. |
| NOT COVERED | A planned suite ran but had no tagged test for this AC. |
| NOT VERIFIABLE / OUT OF SCOPE | The plan says so, with a reason. |

Test results are counted separately as passed, failed and skipped. Suites are `ran`,
`blocked` or `not-started`. A skipped, blocked, withheld or not-started test is never a pass.

Each result also says where it came from: *committed* (a reviewed test), *unpromoted*, or
*unknown* when the framework's JUnit output does not name the file and an unpromoted file ran
in that suite. Unknown is treated as unreviewed.

## Verdict rules (computed by `report.py`, in this order)

**NOT VERIFIED** (exit 4). Executed tests produced failures:
- a test tagged to an in-scope AC failed (also when that AC is UNRESOLVED)
- an existing (untagged) regression test failed
- a suite ran, exited non-zero and produced no results (crash or timeout)

**INCOMPLETE** (exit 3). Nothing failed, but something could not be shown:
- Gate 1 has open questions (any AC UNRESOLVED, or a story-level question)
- `plan.json` has problems (`plan --check`)
- an in-scope AC is BLOCKED or NOT COVERED
- an AC is marked `not-verifiable`
- a suite was blocked or could not start
- a test file is still `@ai-proposed` (in pipeline mode it was also withheld)
- the evidence came from an interactive run, not a pipeline run
- a pipeline run had uncommitted changes to application code (`guardrails.protected_paths`)
  or to reviewed tests, so the evidence is not from the committed revision

**VERIFIED** (exit 0). None of the above. Every in-scope AC has passing, traced evidence from
a pipeline run of reviewed tests on a clean revision.

`out-of-scope` ACs (with a reason) don't block a verdict; they are listed in the report.

Exit code 1 means a usage or whole-run guardrail error (bad config, literal secret in config,
production environment); 2 means a `gate1`/`plan` check found open items.

## Findings

`report` also writes `findings.json`, one entry per failure, for developers: story, AC, test,
expected and observed (only when the framework printed them, never inferred), message, full
failure output, screenshots, traces, the exact suite command and a focused re-run command
where the framework is known, environment, revision, timestamp. Secrets are redacted.

| Classification | When |
|---|---|
| confirmed failure | a reviewed (committed) test failed |
| suspected defect (unreviewed test) | an unpromoted test, or one of unknown origin, failed: triage before treating it as a product defect |
| requirement ambiguity | the failing test belongs to an AC with an open Gate 1 question |
| could not produce results | a suite crashed or timed out without results |

## Approving a non-VERIFIED story

Allowed, because shipping decisions belong to people, but `approve` requires `--note`
explaining why. The note and the verdict at the time are kept in `gate3-approval.json` and
posted to Jira.

## Compatibility

Verdict names and exit codes 0/3/4 are unchanged. One behaviour changed on purpose
(INTENT-001): a pipeline run with unpromoted tests used to stop with exit 1 before running
anything. It now withholds those files, runs the rest, and exits 3 (INCOMPLETE). CI that
treated any non-zero exit as "not verified" behaves the same.
