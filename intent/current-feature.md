# Current Feature

## Outcome
A tester, developer or SRE can ask Claude to verify a Jira story and get back, for every
acceptance criterion, traced evidence from the team's own test frameworks or a stated
reason there is none, with a person deciding at three gates (clarify, promote, approve).

## Inputs
- A Jira story (simulated in `jira/` for the demo; Jira REST optional)
- The repository: code, existing tests, and the test commands in `verify.config.json`

## Outputs
- `verification/<KEY>/`: Gate 1 clarifications, verification plan, report, evidence
- Tests in the repo's own framework, tagged by AC and marked `@ai-proposed` until promoted
- A results comment on the story

## Success / Evidence
- Running the loop on `SHOP-142` against the demo app produces a report whose verdict
  follows from the evidence (see `docs/sample-run/SHOP-142`).
- The same plan and commit give the same verdict when re-run.
- Pipeline mode refuses unreviewed tests; runs refuse production URLs.

## Constraints / Boundaries
- Python standard library only for the engine. No pip installs.
- Never add a test framework; use the team's. JUnit XML is the common output.
- AI plans and writes; it does not approve its own tests or the story.

## Delta · INTENT-001 Autonomous evidence-based verification

Full intent: `intent/INTENT-001-autonomous-verification.md`.

**Observation:** On the first real SHOP-142 run, verification waited on product-owner answers
before any test ran, and pipeline mode refused the whole run because two test files were still
`@ai-proposed`. People were asked to approve steps that carry no risk.

**Keep:** the deterministic engine and its verdicts (VERIFIED, INCOMPLETE, NOT VERIFIED) and
exit codes 0/3/4; tests linked to criteria by title; the team's own frameworks and JUnit XML;
the guardrails; promotion (Gate 2) and approval (Gate 3) as human decisions.

**Change:**
- Clarification is an exception, not a gate before testing. An open question marks only its
  own criterion UNRESOLVED (never PASS); every other criterion is tested normally.
- A blocked operation skips only itself, with the reason recorded; authorised work continues.
- Pipeline mode withholds unpromoted test files instead of refusing the run.
- Each failure produces a developer-facing finding, classed as confirmed, suspected or ambiguity.

**New boundary:** a missing answer or authorisation is never read as permission. Production,
shared-data writes outside permitted environments, product-code changes, promotion, risk
acceptance and approval stay with people. Enforcement is in the engine, not in the prompt.

**Evidence:** `python3 -m unittest discover -s tests/verifykit` passes; SHOP-142 runs in both
modes; a story with an ambiguous criterion still runs its unrelated tests; a blocked suite is
reported as BLOCKED while others run; pipeline mode runs with stdin closed; verdicts match the
previous engine wherever the intent does not change them. Evidence is kept in
`docs/validation/INTENT-001/`.

## Delta · INTENT-002 Real Jira, shipped as a plugin

Full intent: `intent/INTENT-002-real-jira-plugin.md`.

**Observation:** EXPERIMENT-001 (IDS-3) found four defects on the real-Jira path, and the
verification skills were not in the shipped plugin.

**Change:** parse REST v2 wiki-markup criteria; refuse to plan or run a story with no criteria;
recognise `ACn` class tags; ship `.claude/` as the `ai-feature-verification` plugin with
path-independent skills; `init` writes the cloud Jira block from the environment.

**Evidence:** engine unit tests pass; the IDS-3 suite passes except the live test, which runs
only where `JIRA_*` is set.
