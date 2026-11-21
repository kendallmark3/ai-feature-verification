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
- Use the team's test framework. Only when a project has none, add the default (Playwright for
  web, pytest for Python), and only after a person approves it (INTENT-003). JUnit XML is the
  common output.
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

## Delta · INTENT-003 Saturday-ready verification

Full intent: `intent/INTENT-003-saturday-ready.md`.

**Observation:** Next Saturday's build is a Spring Boot API with a React front end. Measured
on 2026-11-21: Maven Surefire drops JUnit 5 `@DisplayName`, so `SAT-1 AC-1` tags are lost
unless the phrased-name reporter is configured; with it, the engine reads them. A fresh React
front end has no tests, and the engine can't create the Jira story.

**Change (decided by Mark Kendall, 2026-11-21):** when a project has no test framework, propose
the default (Playwright for web, pytest for Python) and add it only after a named person
approves. Make Java tagging work, detect both apps in one repo, decide how the Saturday story
gets into Jira, and rehearse on `samples/intake-starter/` (SAT-0).

**Evidence:** the dress rehearsal reaches a real verdict with Java tests tagged; nothing is
added or changed without approval; SHOP-142 and IDS-3 verdicts unchanged.

**Result (2026-11-21):** done to the stop point. `init` finds `backend/` and `frontend/`,
reports the missing Surefire reporter and the untested front end, and changes nothing.
`verify.py frameworks <KEY> --propose | --approve --by NAME | --apply` adds Playwright (web) or
pytest (Python), or the Maven reporter block, only after a named person approves; the approval
(name, time, proposal hash) is in `verification/<KEY>/framework-proposal.json`. Java results map
to their `.java` file for Gate 2 labels. Dress rehearsal `samples/intake-starter/` (SAT-0,
approved by Mark Kendall): AC-1–AC-5 all PASS from tests that ran (3 JUnit via MockMvc, 2
Playwright), Java tags counted; verdict INCOMPLETE only for Gate 2 and interactive mode. Before
the reporter, the same three Java tests passed but counted as untagged. 96 engine tests pass;
SHOP-142 and IDS-3 verdicts unchanged when their last runs are re-judged. Gradle still unmeasured.
