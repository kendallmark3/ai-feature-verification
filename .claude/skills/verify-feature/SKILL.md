---
name: verify-feature
description: Verify that a Jira story is actually done by planning against its acceptance criteria, writing tests in the repo's own framework, running them deterministically, and reporting evidence per criterion with three human gates. Use when asked to verify, test, QA or check a story, ticket or feature ("verify SHOP-142", "is this story done?", "test this ticket").
---

# Verify Feature

AI plans; the repository's own test frameworks execute; people decide at three gates.
Every acceptance criterion (AC) ends with traced evidence or an explicit reason it has none.

The engine is `scripts/verify.py` (Python standard library only). It never decides
anything: it pulls the story, runs the commands in `verify.config.json`, parses JUnit
XML, and computes coverage. You do the thinking it can't: judging gaps, writing the
plan, writing tests, triaging failures, explaining results.

Run every command from the repository root:

```bash
V=.claude/skills/verify-feature/scripts/verify.py
```

## Before you start

- `verify.config.json` must exist at the root. If not, run `python3 $V init`, show the
  person the suggested suites, and wait for them to confirm the commands. Never guess a
  test command and run it.
- Read `references/guardrails.md`. Never point a run at production, never put secrets in
  files, never install packages or change CI without asking.

## The loop

Work through these in order. Track them in the task list.

1. **Pull the story.** `python3 $V story <KEY>`. Check the AC IDs it assigned look right.
2. **Inspect the repo.** `python3 $V inspect <KEY>`. Then read the existing tests for the
   area the story touches and the code they exercise, so new tests follow the team's
   conventions (file layout, helpers, selectors, fixtures).
3. **Gate 1 · Clarify.** Load the `clarify-story` skill and follow it. Do not plan or write
   tests until `python3 $V gate1 <KEY> --check` passes. Answers come from people only.
4. **Plan.** `python3 $V plan <KEY> --init`, then edit `verification/<KEY>/plan.json`
   (schema: `references/plan-schema.md`): copy each Gate 1 answer into `clarified_as`, add
   checks with a configured `suite` and `expected_evidence`, and mark anything that still
   can't be tested `not-verifiable` with a reason. Run `plan <KEY> --check` until clean,
   then `plan <KEY> --render` and show the person `VERIFICATION_PLAN.md`.
5. **Write tests.** In the repo's existing framework only (`references/framework-adapters.md`).
   Tag every test title with the story key and AC (`SHOP-142 AC-3 ...`, see
   `references/ac-tagging.md`) and put `@ai-proposed <KEY>` in a header comment of each file
   you create or change. Tests encode the *clarified* intent. Never weaken an assertion to
   match current behaviour, and never change product code to make a test pass.
6. **Interactive run.** `python3 $V run <KEY> --mode interactive`, then
   `python3 $V evidence <KEY>` and `python3 $V report <KEY>`. Triage each failure with
   `references/triage.md`: fix your own test bugs and re-run; report product defects, don't fix them.
7. **Gate 2 · Promote.** Load the `promote-tests` skill. Pipeline mode refuses to run while
   any file is still `@ai-proposed`.
8. **Pipeline run.** `python3 $V all <KEY> --mode pipeline` (or the `verify` GitHub Actions
   workflow). Only pipeline evidence can reach a `VERIFIED` verdict.
9. **Close the loop.** `python3 $V post <KEY>` posts the summary to Jira. Show the person the
   verdict, the per-AC table, and any defects in plain words.
10. **Gate 3 · Approve.** The person decides. Give them the `approve` command from the
    report. Don't run it unless they tell you to in this conversation, with their name and
    decision.

## Rules that hold throughout

- Report only what `evidence.json` and `report.json` say. Never describe a test as passing
  that the evidence doesn't show, and never round "mostly passing" up to done.
- The three verdicts are `VERIFIED`, `INCOMPLETE` and `NOT VERIFIED`; their exact meaning is
  in `references/gates.md`. Don't soften them.
- A story with failing or unverifiable criteria is a useful result, not a failure of the skill.
- Commit the plan, Gate 1 file and report with the tests (`verification/<KEY>/`); raw run
  folders are ignored by git.

## References

- `references/gates.md` — what each gate checks, who acts, and the verdict rules
- `references/plan-schema.md` — `plan.json` fields with an example
- `references/ac-tagging.md` — how tests are linked to criteria
- `references/framework-adapters.md` — getting JUnit XML from each framework
- `references/triage.md` — test bug or product defect
- `references/guardrails.md` — what the runner refuses and why
- `references/jira.md` — local (simulated) and cloud adapters
- `assets/verify.config.example.json`, `assets/plan.example.json`, `assets/test-headers.md`
