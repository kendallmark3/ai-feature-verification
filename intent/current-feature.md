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
