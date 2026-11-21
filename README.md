# AI-Assisted Feature Verification

Ask Claude "verify SHOP-142" and get back, for every acceptance criterion, traced evidence
from **your own test frameworks**, or a stated reason there is none. It runs every authorised
test without stopping for approvals, and escalates only what needs a person: open requirement
questions, blocked operations, tests awaiting review, and acceptance. AI plans; deterministic
code executes and judges; people decide.

Built on [intent-drive-starter](https://github.com/kendallmark3/intent-drive-starter)
(its Progressive Intent loop, hooks and skills are still here; see
[docs/intent-drive-starter-README.md](docs/intent-drive-starter-README.md)).

```
Jira story ─► Clarify ─► Plan (AC → test → evidence) ─► Tests in your framework ─► Run ─► Report + findings
                 │  open questions recorded,                  @ai-proposed            │        │
                 │  only their ACs UNRESOLVED                                         │        ▼
                 ▼                                                                    │   Gate 3 Approve
       Gate 1: owner answers ─────────────────────────────── (any time) ──────────────┘   (person)
       Gate 2: reviewer promotes tests ── pipeline runs reviewed tests only; unpromoted are withheld
```

**Runs automatically:** reading the story and code, planning, writing new tests, running every
authorised suite, collecting evidence, writing the report and developer findings.
**Needs a person:** answering requirement questions, promoting tests into the regression
suite, accepting risk or the story, and anything a guardrail blocks (production, shared-data
writes outside permitted environments, product-code changes). A missing answer or permission
is never treated as one.

Full diagram: [docs/architecture.md](docs/architecture.md).

## What's in here

| Path | What |
|---|---|
| `.claude/skills/verify-feature/` | The main skill: `SKILL.md`, `scripts/verify.py` + `verifykit/` (Python stdlib only), `references/`, `assets/` |
| `.claude/skills/clarify-story/` | Gate 1 skill: record gaps and who owns each answer, without holding up testing |
| `.claude/skills/promote-tests/` | Gate 2 skill: review brief for AI-proposed tests |
| `verify.config.json` | Your suites (the commands you already run), environments, guardrails, Jira adapter |
| `jira/SHOP-142.json` | Simulated Jira story. Deliberately ordinary, not cooked |
| `jira/IDS-3.json`, `tests/ids3/` | A real Jira Cloud story (snapshot) and the tests the harness ran against its own Jira integration (EXPERIMENT-001) |
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

Claude pulls the story, inspects the repo, records any questions for the product owner,
plans, writes tagged tests in the demo app's own frameworks, runs everything it is allowed to,
and comes back with the verdict, a per-criterion table and developer findings. It doesn't stop
to ask. What it brings back for you: open questions (each criterion they affect is shown
UNRESOLVED), tests waiting for review (**Gate 2**), anything blocked and why, and the
acceptance decision (**Gate 3**).

### Or drive the engine by hand

```bash
V=.claude/skills/verify-feature/scripts/verify.py
python3 $V story SHOP-142            # pull, assign AC IDs
python3 $V inspect SHOP-142          # frameworks, tests, AC tags
python3 $V gaps SHOP-142             # Gate 1 questions → verification/SHOP-142/gate1-clarifications.md
python3 $V gate1 SHOP-142 --check    # open questions by AC and owner (exit 2 while any are open)
python3 $V plan SHOP-142 --init      # then fill plan.json; --check; --render
python3 $V run SHOP-142 --mode interactive
python3 $V evidence SHOP-142 && python3 $V report SHOP-142   # also writes findings.json
python3 $V all SHOP-142 --mode pipeline   # reviewed tests only; unpromoted files withheld
python3 $V proposed                  # Gate 2: files still @ai-proposed
python3 $V promote <file> --by "Your Name" --story SHOP-142
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
| **INCOMPLETE** | Nothing failed, but something could not be shown: open questions (UNRESOLVED ACs), blocked or withheld tests, uncovered or unverifiable ACs, unpromoted tests, interactive-only evidence, or a pipeline run on uncommitted code | 3 |
| **NOT VERIFIED** | A tagged test or an existing regression test failed, or a suite crashed without results | 4 |

Exit 1 is a usage or whole-run guardrail error (for example a production environment). The
report separates passed, failed, skipped, blocked, withheld and unresolved; none but *passed*
counts as passing. Each failure in `findings.json` is classed as a **confirmed failure**
(reviewed test), a **suspected defect** (unreviewed test, triage first) or a **requirement
ambiguity** (open question on that AC). Rules: `.claude/skills/verify-feature/references/gates.md`.

**Changed in INTENT-001:** a pipeline run with unpromoted tests used to stop with exit 1 before
running anything. It now withholds them, runs the rest and exits 3. Everything else keeps its
meaning. Validation evidence: `docs/validation/INTENT-001/`.

## Using it on another repo

Install it as a Claude Code plugin and point it at your Jira (full guide: [install-plugin.md](install-plugin.md)):

```bash
claude plugin marketplace add kendallmark3/ai-feature-verification
claude plugin install ai-feature-verification@ai-feature-verification
export JIRA_BASE_URL="https://your-site.atlassian.net" JIRA_EMAIL="you@example.com" JIRA_API_TOKEN="…"
```

Then, in your repo: "Verify PROJ-12". The first run writes `verify.config.json` from the
frameworks it finds (pytest, Jest, Vitest, Playwright, Cypress, Maven, Gradle, Go, .NET) and
waits for you to confirm each suite's command. Tag tests with `<KEY> AC-n` in their titles,
or name the class `Test..._ACn`. The plugin is the `.claude/` folder of this repo; the
marketplace entry is `.claude-plugin/marketplace.json`.

## Deploying the demo to AWS (optional)

Not needed to see it work: Playwright starts the app locally. If you want the
DEV/UAT path, deploy `demo-app` anywhere that runs Node (App Runner, Elastic Beanstalk, or
an EC2 box with `npm ci && npm run build && npm start`, port 4310), then:

```bash
export UAT_BASE_URL=https://<your-uat-host>
python3 .claude/skills/verify-feature/scripts/verify.py run SHOP-142 --env uat
```

The API suite always runs in-process; the e2e suite runs against `BASE_URL`. A URL
containing `prod` or `production` is refused. A suite marked `"writes_shared_data": true`
is blocked in any environment that doesn't set `"allow_shared_data_writes": true`.
