# INTENT-002 · Real Jira, shipped as a plugin

## Outcome
An engineer installs the `ai-feature-verification` plugin, points it at a Jira Cloud site
with their own API token, says "verify IDS-5", and the harness pulls the real story, extracts
its acceptance criteria and runs the full loop in their repository.

## Observation (from EXPERIMENT-001, IDS-3)
- REST v2 returns descriptions as wiki markup; `# item` lists were read as headings → 0 ACs.
- An empty plan passed `plan --check`, and `run` executed suites for a story with no ACs.
- The documented pytest class tag (`TestIDS3_AC4`) was not recognised.
- The verification skills lived only in `.claude/skills/`; the repo's plugin manifest shipped
  the intent-drive-starter instead, and the skills hard-coded `.claude/skills/...` paths.

## Inputs
- Jira Cloud site URL, the engineer's Atlassian email and API token, as environment variables
- The engineer's repository and its existing test commands

## Outputs
- Fixes for the four defects, with tests
- A plugin (`.claude/` is the plugin root) and marketplace entry, installable with two commands
- `verify.py init` writes the cloud Jira block when `JIRA_BASE_URL` is set
- Install and Jira setup docs

## Success / Evidence
- `python3 -m unittest discover -s tests/verifykit` passes, including new tests for each defect.
- The IDS-3 suite (`tests/ids3/`) passes with no AC failures; only the live test skips here.
- The live test passes on a machine with `JIRA_*` set (Mark runs it; it is skipped, never faked, elsewhere).
- `claude plugin validate .` (or the manifest check in tests) accepts the plugin and marketplace.

## Constraints / Boundaries
- Engine stays Python standard library only. Tests stay stdlib unittest.
- Credentials only from the environment; `${VAR}` references in config; never in files or chat.
- Simulated Jira (`jira/*.json`, SHOP-142) keeps working unchanged.
- Don't change guardrails, CI workflows, or demo-app product code.
- No new Jira writes besides the existing `post` / `approve` comment path.
