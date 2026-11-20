# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Repository Rules
Read intent/current-feature.md first, including any deltas appended to it.
Run hooks/pre-implement.sh before implementing.
Build the smallest useful delta, then let the human observe it and decide: continue or stop.
Always write tests.
Respect architecture (docs/architecture.md).

## Feature verification
- To verify a story, use the `verify-feature` skill. Gate 1 is `clarify-story`, Gate 2 is `promote-tests`.
- The engine is `.claude/skills/verify-feature/scripts/verify.py` (stdlib Python). Run it from the repo root.
- The demo app is `demo-app/` (React + Node, Playwright + node:test). Story: `jira/SHOP-142.json`.
- Never answer Gate 1 questions, promote tests or approve a story on your own. People do that.
- Don't change product code in `demo-app/server` or `demo-app/web` while verifying; report defects instead.

## Commands

Engine and repo checks (the same ones CI runs in `.github/workflows/ci.yml`):

```bash
python3 -m unittest discover -s tests/verifykit -v                    # engine unit tests
python3 -m unittest discover -s tests/verifykit -k Guardrails         # one test class or method
bash tests/pre-implement.test.sh                                      # tests for hooks/pre-implement.sh
bash hooks/pre-implement.sh [intent-file]                             # gate before implementing
```

Demo app (run from `demo-app/`; needs Node 20+, `npm install`, `npx playwright install chromium` or `export PW_CHANNEL=chrome`):

```bash
npm run test:api                                   # node:test → reports/api-junit.xml
npx playwright test                                # desktop + mobile projects → reports/e2e-junit.xml
npx playwright test -g "SHOP-142 AC-3"             # one test by title
npx playwright test --project=desktop
node --test tests/api/cart.test.mjs                # one API file
npm run build && npm start                         # app on port 4310
```

Playwright starts the app itself unless `BASE_URL` is set; then it targets that DEV/UAT host.

Engine CLI (`V=.claude/skills/verify-feature/scripts/verify.py`): `story`, `inspect`, `gaps`,
`gate1 --check`, `plan --init|--check|--render`, `run --mode interactive|pipeline [--env uat]`,
`evidence`, `report`, `proposed`, `promote`, `all`, `post`, `approve`, `init`. See README.md for the full sequence.

## Architecture

The core split: **Claude plans and writes; deterministic stdlib Python executes and judges; people decide at gates.** Same story + plan + commit must give the same verdict without the model.

- `verify.py` is a thin argparse front end over `scripts/verifykit/`: `jira.py`/`story.py` pull the story and assign AC IDs; `gaps.py` produces rule-based Gate 1 questions; `plan.py` validates `plan.json` (schema in `references/plan-schema.md`); `guardrails.py` + `runner.py` run the suites from `verify.config.json`; `evidence.py` parses JUnit XML and maps tests to ACs; `report.py` computes the verdict; `promote.py` handles Gate 2.
- `verify.config.json` (repo root) is the contract between the engine and the app: each suite is a command, a cwd, and JUnit output paths. The engine never knows the framework beyond that; JUnit XML is the common format.
- Tests are linked to criteria **only by title**: `SHOP-142 AC-3 ...`. Tests carrying no AC ID are treated as regression tests, and a failure there still makes the verdict NOT VERIFIED. A different story key in a title makes the test ignored for this story.
- New/changed test files carry `@ai-proposed <KEY>` in a header comment until a person promotes them; pipeline mode refuses to run while any remain. Only pipeline evidence can produce `VERIFIED`.
- Verdict exit codes from `report`/`all`: 0 VERIFIED, 3 INCOMPLETE, 4 NOT VERIFIED.
- Guardrails (`references/guardrails.md`): commands run without a shell and must start with an allow-listed word; URLs matching `prod`/`production` are refused; secret-like config keys must be `${ENV_VAR}`. Don't edit guardrails or CI workflows without asking.
- Output goes to `verification/<KEY>/` (commit plan, Gate 1 file, report; `runs/` is gitignored). `docs/sample-run/SHOP-142/` is a complete reference run.
- The engine must stay Python standard library only (no pip). Never add a test framework to a target repo; use the one it has.

Leftovers from the intent-drive-starter template (Progressive Intent loop): `intent/`, `hooks/` (a plugin `PreToolUse` hook on Edit/Write runs `pre-implement-hook.sh`), root `skills/`, `agents/`, `context/`, `templates/`, `.claude-plugin/`.
