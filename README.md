# AI-Assisted Feature Verification

Ask Claude "verify SHOP-142" and get back, for every acceptance criterion, traced evidence
from **your own test frameworks**, or a stated reason there is none. People decide at three
gates. AI plans; deterministic code executes.

Built on [intent-drive-starter](https://github.com/kendallmark3/intent-drive-starter)
(its Progressive Intent loop, hooks and skills are still here; see
[docs/intent-drive-starter-README.md](docs/intent-drive-starter-README.md)).

```
Jira story ─► Gate 1 Clarify ─► Plan (AC → test → evidence) ─► Tests in your framework
   ▲              (PO answers)                                        │ @ai-proposed
   │                                                                   ▼
   └── results comment ◄── Report + verdict ◄── Pipeline run ◄── Gate 2 Promote ◄── Interactive run
                               │                                  (reviewer)
                               ▼
                         Gate 3 Approve (person)
```

Full diagram: [docs/architecture.md](docs/architecture.md).

## What's in here

| Path | What |
|---|---|
| `.claude/skills/verify-feature/` | The main skill: `SKILL.md`, `scripts/verify.py` + `verifykit/` (Python stdlib only), `references/`, `assets/` |
| `.claude/skills/clarify-story/` | Gate 1 skill: find gaps, get answers before anything runs |
| `.claude/skills/promote-tests/` | Gate 2 skill: review brief for AI-proposed tests |
| `verify.config.json` | Your suites (the commands you already run), environments, guardrails, Jira adapter |
| `jira/SHOP-142.json` | Simulated Jira story. Deliberately ordinary, not cooked |
| `demo-app/` | React + Node.js shop to verify against. node:test (API) + Playwright (desktop + mobile) |
| `docs/sample-run/SHOP-142/` | A complete run: questions, plan, tests, logs, screenshots, report |
| `tests/verifykit/` | Unit tests for the engine (`python3 -m unittest discover -s tests/verifykit`) |
| `.github/workflows/verify.yml` | Pipeline mode in GitHub Actions |

## Run it locally

Needs Node 20+ and Python 3.10+. Nothing to pip install.

```bash
cd demo-app
npm install
npx playwright install chromium      # or use installed Chrome: export PW_CHANNEL=chrome
cd ..
```

Then open the repo in Claude Code and say:

> Verify SHOP-142.

Claude will pull the story, inspect the repo, and stop at **Gate 1** with questions for you
to answer as the product owner. After that it plans, writes tagged tests in the demo app's
own frameworks, runs them, and stops at **Gate 2** for you to review and promote. Then the
pipeline run, the report, and the comment on the (simulated) Jira story. **Gate 3** is yours.

### Or drive the engine by hand

```bash
V=.claude/skills/verify-feature/scripts/verify.py
python3 $V story SHOP-142            # pull, assign AC IDs
python3 $V inspect SHOP-142          # frameworks, tests, AC tags
python3 $V gaps SHOP-142             # Gate 1 questions → verification/SHOP-142/gate1-clarifications.md
python3 $V gate1 SHOP-142 --check    # passes when every question has an Answer:
python3 $V plan SHOP-142 --init      # then fill plan.json; --check; --render
python3 $V run SHOP-142 --mode interactive
python3 $V evidence SHOP-142 && python3 $V report SHOP-142
python3 $V proposed                  # Gate 2: files still @ai-proposed
python3 $V promote <file> --by "Your Name" --story SHOP-142
python3 $V all SHOP-142 --mode pipeline
python3 $V post SHOP-142             # comment on the story
python3 $V approve SHOP-142 --by "Your Name" --decision approved|rejected --note "..."
```

To replay the sample without Claude: copy `docs/sample-run/SHOP-142/tests/discount.test.mjs`
to `demo-app/tests/api/` and `discount.spec.js` to `demo-app/tests/e2e/`, and copy the
sample's `story.json`, `gate1-*`, `plan.json` into `verification/SHOP-142/`.

## Verdicts

| Verdict | Means | `report` / `all` exit code |
|---|---|---|
| **VERIFIED** | Every in-scope AC has passing, traced evidence from a pipeline run of reviewed tests | 0 |
| **INCOMPLETE** | Nothing failed, but something is missing: open Gate 1 questions, uncovered or unverifiable ACs, unpromoted tests, or interactive-only evidence | 3 |
| **NOT VERIFIED** | A tagged test or an existing regression test failed | 4 |

## Using it on another repo

1. Copy `.claude/skills/verify-feature`, `clarify-story` and `promote-tests` into that repo's `.claude/skills/`.
2. From its root: `python3 .claude/skills/verify-feature/scripts/verify.py init` writes a
   starter `verify.config.json` from the frameworks it finds (pytest, Jest, Vitest,
   Playwright, Cypress, Maven, Gradle, Go, .NET). Check each suite's command and JUnit path.
3. Point `jira` at your instance (see `.claude/skills/verify-feature/references/jira.md`) or
   keep the local folder.
4. Tag tests with `<KEY> AC-n` in their titles.

## Deploying the demo to AWS (optional)

Not needed to see it work: Playwright starts the app locally. If you want the
DEV/UAT path, deploy `demo-app` anywhere that runs Node (App Runner, Elastic Beanstalk, or
an EC2 box with `npm ci && npm run build && npm start`, port 4310), then:

```bash
export UAT_BASE_URL=https://<your-uat-host>
python3 .claude/skills/verify-feature/scripts/verify.py run SHOP-142 --env uat
```

The API suite always runs in-process; the e2e suite runs against `BASE_URL`. A URL
containing `prod` or `production` is refused.
