---
name: verify-feature
description: Verify that a Jira story is actually done by planning against its acceptance criteria, writing tests in the repo's own framework, running every authorised test deterministically, and reporting evidence per criterion. Runs without stopping for approvals; open questions, blocked operations and unreviewed tests become recorded exceptions for the right person. Use when asked to verify, test, QA or check a story, ticket or feature ("verify SHOP-142", "is this story done?", "test this ticket").
---

# Verify Feature

AI plans; the repository's own test frameworks execute; people decide only what needs human
authority. Every acceptance criterion (AC) ends with traced evidence or an explicit reason it
has none.

**Run the whole loop without waiting for approval.** Your job is to produce evidence, not to
make product or business decisions. Escalate only genuine exceptions, as records the right
person can act on:

| Exception | What you do | Who resolves it |
|---|---|---|
| An AC is ambiguous | Record the question (Gate 1 file). Test everything else. Don't invent the expected behaviour. | Story owner answers |
| A suite is blocked by a guardrail | Nothing: the engine skips it, records why, runs the rest | A person changes config, through review |
| A test you wrote is unpromoted | Run it interactively (it is labelled unreviewed). Pipeline withholds it. | Reviewer promotes (Gate 2) |
| A test fails | Triage it. Report product defects; fix only your own test bugs | Developer |
| The story is ready to accept | Present the evidence | Accountable person approves (Gate 3) |

The engine is `scripts/verify.py` (Python standard library only). It never decides
anything: it pulls the story, runs the commands in `verify.config.json`, parses JUnit
XML, and computes coverage. You do the thinking it can't: judging gaps, writing the
plan, writing tests, triaging failures, explaining results.

Run every command from the root of the repository being verified. The engine ships inside
this skill, so take its path from this skill's base directory (shown when the skill loads;
in the ai-feature-verification repo it is `.claude/skills/verify-feature`, and installed as a
plugin it is in the plugin's install folder):

```bash
V="<this skill's base directory>/scripts/verify.py"
```

## Before you start

- `verify.config.json` must exist at the root. If not, run `python3 $V init`, show the
  person the suggested suites, and wait for them to confirm the commands. Never guess a
  test command and run it.
- Read `references/guardrails.md`. Never point a run at production, never put secrets in
  files, never install packages or change CI without asking.
- **Real Jira** (`references/jira.md`): the `cloud` adapter reads `JIRA_BASE_URL`,
  `JIRA_EMAIL` and `JIRA_API_TOKEN` from the environment. If they are exported when `init`
  runs, it configures the cloud adapter for you. If `story` fails because they are missing,
  tell the person to export them in their own shell (an Atlassian API token, from
  id.atlassian.com → Security → API tokens) and restart Claude Code. **Never ask for the
  token in chat and never write it into any file.**

## The loop

Work through these in order without pausing for confirmation. Track them in the task list.

1. **Pull the story.** `python3 $V story <KEY>`. Check the AC IDs it assigned look right.
   If it finds no criteria, stop: Gate 1 records NO_ACCEPTANCE_CRITERIA, and `plan` and
   `run` refuse until the story in Jira has them (a numbered list under an "Acceptance
   Criteria" heading in the description). Tell the person exactly that.
2. **Inspect the repo.** `python3 $V inspect <KEY>`. Then read the existing tests for the
   area the story touches and the code they exercise, so new tests follow the team's
   conventions (file layout, helpers, selectors, fixtures).
3. **Clarify (exception-based).** Load the `clarify-story` skill and follow it: record the
   questions and who owns each answer, then **carry on**. Don't wait for answers.
   `python3 $V gate1 <KEY> --check` exits 2 while questions are open; that is information,
   not a stop. An open question leaves only its own criteria UNRESOLVED.
4. **Plan.** `python3 $V plan <KEY> --init` (skip if `plan.json` exists), then edit
   `verification/<KEY>/plan.json` (schema: `references/plan-schema.md`). Copy each Gate 1
   answer into `clarified_as` and add checks with a configured `suite` and
   `expected_evidence`. For an AC with an open question, plan checks only for the parts that
   don't depend on the answer; if nothing can be tested without guessing, leave `checks`
   empty (allowed while the question is open). Mark anything that can't be tested
   `not-verifiable` with a reason. Run `plan <KEY> --check` until clean, then
   `plan <KEY> --render`.
5. **Write tests.** In the repo's existing framework only (`references/framework-adapters.md`).
   Tag every test title with the story key and AC (`SHOP-142 AC-3 ...`, see
   `references/ac-tagging.md`). Put generated tests in **new files** with `@ai-proposed <KEY>`
   in a header comment. Never edit or overwrite a reviewed test file (one without the marker):
   the engine flags edited reviewed tests and the run can't verify. Tests encode the
   *clarified* intent. Never weaken an assertion to match current behaviour, and never change
   product code to make a test pass.
6. **Run.** `python3 $V all <KEY> --mode interactive` runs every authorised suite, including
   your unpromoted tests (labelled *unreviewed* in the evidence). Suites the guardrails block
   are skipped with a reason; the rest run. Triage each failure with `references/triage.md`:
   fix your own test bugs and re-run; report product defects, don't fix them.
7. **Pipeline run.** `python3 $V all <KEY> --mode pipeline` (or the `verify` GitHub Actions
   workflow). It runs reviewed tests only: unpromoted files are withheld for the run and put
   back afterwards, and their criteria show BLOCKED. Only pipeline evidence from reviewed
   tests can reach `VERIFIED`. Never needs a person at the keyboard.
8. **Report.** Show the person the verdict, the per-AC table, `findings.json` in plain words
   (confirmed failures, suspected defects, requirement ambiguities), and the exceptions with
   their owners: open questions, blocked suites, tests awaiting review.
9. **Gate 2 · Promote** (when the person wants unreviewed tests in the regression suite):
   load the `promote-tests` skill to prepare the review. Promotion is theirs.
10. **Gate 3 · Approve.** The person decides. Give them the `approve` command from the
    report. Don't run it unless they tell you to in this conversation, with their name and
    decision. `python3 $V post <KEY>` posts the summary to Jira when they want it there.

## Rules that hold throughout

- Report only what `evidence.json`, `report.json` and `findings.json` say. Never describe a
  test as passing that the evidence doesn't show, and never round "mostly passing" up to done.
  Skipped, blocked, withheld and unresolved are not passes.
- A missing answer or permission is never permission. Don't answer Gate 1 questions, promote
  tests, accept risk or approve the story yourself, and don't change guardrails to unblock a suite.
- The three verdicts are `VERIFIED`, `INCOMPLETE` and `NOT VERIFIED`; their exact meaning is
  in `references/gates.md`. Don't soften them.
- A story with failing or unverifiable criteria is a useful result, not a failure of the skill.
- Commit the plan, Gate 1 file and report with the tests (`verification/<KEY>/`); raw run
  folders are ignored by git.

## References

- `references/gates.md` — what runs automatically, what each gate checks, who acts, and the verdict rules
- `references/plan-schema.md` — `plan.json` fields with an example
- `references/ac-tagging.md` — how tests are linked to criteria
- `references/framework-adapters.md` — getting JUnit XML from each framework
- `references/triage.md` — test bug or product defect
- `references/guardrails.md` — what the runner blocks, withholds or refuses, and why
- `references/jira.md` — local (simulated) and cloud adapters
- `assets/verify.config.example.json`, `assets/plan.example.json`, `assets/test-headers.md`
