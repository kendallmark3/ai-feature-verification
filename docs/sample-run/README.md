# Sample run · SHOP-142

What one full pass of the loop produced on 2026-11-19, kept so you can see the output
without running anything. **The PO answers and the Gate 2 reviewer are simulated** and
labelled that way in the files.

This run predates INTENT-001, so it stops at each gate; the current skill runs straight
through and records open items as exceptions. For a run with real product-owner answers, see
`verification/SHOP-142/`. Those answers differ from the simulated ones here (expired codes
accepted, letter case left as accepted risk), so that run finds no defects.

| File | Step |
|---|---|
| `story.json` | 1 · story pulled from `jira/SHOP-142.json`, AC IDs assigned |
| `gate1-clarifications.md` | 3 · Gate 1: 6 rule-based questions + 4 judgement questions (Q-AI-n), all answered |
| `plan.json`, `VERIFICATION_PLAN.md` | 4 · the plan: AC → clarified rule → checks → expected evidence |
| `tests/` | 5 · the tests Claude proposed (shown after promotion) |
| `gate2-promotions.json` | 7 · Gate 2 record |
| `logs/` | 8 · pipeline-mode run logs and manifest |
| `evidence.json`, `report.json`, `VERIFICATION_REPORT.md` | 8 · evidence and verdict |
| `jira-SHOP-142-after-post.json` | 9 · the simulated Jira issue with the posted comment |
| `screenshots/` | three of the Playwright screenshots linked from the report |

## What it found

**Verdict: NOT VERIFIED.**

- **AC-2 fails**: codes are case-sensitive; `save10` is refused. The PO said codes should
  not be case-sensitive (Q-AI-2).
- **AC-3 fails**: the expired code `WELCOME5` is still accepted. The PO said expired codes
  must be refused (Q-AI-1). The discount rules have an `expires` date that nothing checks.
- **AC-4 is not verifiable**: "Should be fast" has no threshold; the PO recorded it as an
  accepted risk.
- AC-1 and AC-5 pass on desktop and a Pixel 7 viewport; the 4 existing regression tests pass.

Neither defect was visible from the story as written. Both came out of Gate 1 questions
raised by reading the code. Paths inside the report point at `verification/SHOP-142/runs/...`,
which is not committed; the copies here are the evidence.
