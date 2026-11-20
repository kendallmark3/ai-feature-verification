# Gates and verdicts

| Gate | When | Who acts | Passes when | Command |
|---|---|---|---|---|
| 1 · Clarify | before planning | Product owner / story owner answers; Claude asks | every question in `gate1-clarifications.md` has an `Answer:` | `verify.py gate1 <KEY> --check` |
| 2 · Promote | after the interactive run, before pipeline | Reviewer (usually via a test-only PR) | no test file under the suites' `test_paths` still says `@ai-proposed` | `verify.py promote <file> --by <name>` |
| 3 · Approve | after the pipeline run | The accountable person (tester, lead, PO) | they record a decision | `verify.py approve <KEY> --by <name> --decision approved\|rejected` |

Claude prepares each gate and stops there. It runs `promote` or `approve` only when a
person tells it to in the conversation, naming themselves and the decision.

## Verdict rules (computed by `report.py`, in this order)

**NOT VERIFIED** — any of:
- a test tagged to an in-scope AC failed
- an existing (untagged) regression test failed
- a suite exited non-zero without producing any results

**INCOMPLETE** — nothing failed, but any of:
- Gate 1 has open questions
- `plan.json` has problems (`plan --check`)
- an in-scope AC has no tagged test in one of its planned suites
- an AC is marked `not-verifiable`
- a test file is still `@ai-proposed`
- the evidence came from an interactive run, not a pipeline run

**VERIFIED** — none of the above. Every in-scope AC has passing, traced evidence from a
pipeline run of reviewed tests.

`out-of-scope` ACs (with a reason) don't block a verdict; they are listed in the report.

## Approving a non-VERIFIED story

Allowed, because shipping decisions belong to people, but `approve` requires `--note`
explaining why. The note and the verdict at the time are kept in `gate3-approval.json` and
posted to Jira.
