# INTENT-001 · Validation evidence

Runs of the real engine against the real demo app: Node 22, `node:test` for the API suite,
Playwright with Chromium for desktop and Pixel 7. Each folder in `runs/` holds the command,
console output, exit code, `run.json`, `report.json`, `findings.json`,
`VERIFICATION_REPORT.md` and, for failures, the screenshots. Reproduce with:

```bash
bash docs/validation/INTENT-001/run-validation.sh /tmp/val [old-engine-dir]
```

Every scenario runs in a scratch copy of the repository, so the committed
`verification/SHOP-142/` from the first real run is not touched. All runs used closed stdin, no
terminal (`setsid`) and `CI=1`, as an unattended runner would.

Validated on 2026-11-20 at commit `dc04629` + this change. Environment note: the browser download
was blocked in the validation sandbox, so `@playwright/test` 1.63.0 was installed there without
saving to match the preinstalled Chromium. `package.json` and the lockfile are unchanged.

**Simulated in these runs, labelled as such:** the Gate 2 reviewer ("Validation reviewer
(simulated)") in 05–07, and an open question in 03 and 06 (the real answer to Q-AI-4 was
removed in the scratch copy). The deliberate failures come from the two files in `fixtures/`,
which assert behaviour nobody asked for, so failures are known in advance.

## Scenarios

| # | Scenario | Engine | Verdict | Exit | What it shows |
|---|---|---|---|---|---|
| 01 | SHOP-142 as merged, interactive | new | INCOMPLETE | 3 | Same verdict, AC statuses, test counts (17 tagged, 4/4 regression) and reasons as the old engine |
| 01 | same | old | INCOMPLETE | 3 | Baseline. Counts 4 unpromoted files because it scans the whole repo (it picked up the validation fixtures); the new engine counts only suite test paths, per `gates.md` |
| 02 | SHOP-142 as merged, pipeline | new | INCOMPLETE | 3 | Runs instead of refusing: withholds the 2 unpromoted files, runs the 4 reviewed regression tests, restores the files. AC-1/2/3/5 BLOCKED (withheld) |
| 02 | same | old | — | 1 | Baseline: refused, nothing ran |
| 03 | Q-AI-4 on AC-2 left open | new | INCOMPLETE | 3 | AC-2 UNRESOLVED; AC-1, 3, 5 PASS; the same 21 tests ran as in 01. Unrelated tests keep running |
| 04 | 2 deliberate failures, interactive | new | NOT VERIFIED | 4 | 3 failures detected (API, Playwright desktop + mobile). All classed *suspected defect (unreviewed test)*: the Playwright one is unpromoted, and the API one is "origin unknown" because node:test's JUnit doesn't name files and an unpromoted file ran in that suite |
| 04 | same | old | NOT VERIFIED | 4 | Same verdict and failing criteria |
| 05 | Sample tests promoted, deliberate reviewed API failure, deliberate unpromoted e2e test | new | NOT VERIFIED | 4 | API failure now *confirmed failure* (every API test reviewed). Unpromoted e2e test withheld, not run |
| 06 | Same failure while AC-2's question is open | new | NOT VERIFIED | 4 | Same failure, classed *requirement ambiguity* and linked to Q-AI-4 |
| 07 | Promoted, clean, pipeline | new | INCOMPLETE | 3 | Every testable AC PASS from reviewed tests on a clean revision. The only reason left is AC-4, which the product owner accepted as not verifiable |
| 08 | Three restricted suites added: `curl` (not allow-listed), a production URL, a shared-data writer in `dev` | new | INCOMPLETE | 3 | All three BLOCKED with their reasons; api and e2e still ran (21 passed, 4/4 regression) |
| 09 | Environment pointing at production | new | — | 1 | Whole run refused before anything executed |

## Required validation (intent §6)

| # | Check | Evidence |
|---|---|---|
| 1 | Engine tests | `unit-tests.txt`: 53 tests (18 existing, 35 new) + hook tests, all pass |
| 2 | Current SHOP-142 demonstration | 01, 02 |
| 3 | API execution | every run: `api` suite, node:test JUnit |
| 4 | Chromium/Playwright execution | every run: `e2e` suite, 16 cases, desktop + Pixel 7, screenshots and traces |
| 5 | Story with an ambiguous criterion | 03, 06 |
| 6 | Unrelated tests keep running | 03 (21 passed, same as 01) |
| 7 | Generated test not promoted | 01 and 04 (runs, labelled unreviewed), 02 and 05 (withheld) |
| 8 | Restricted operation without authorization | 08 (three suites blocked), 09 (production refused) |
| 9 | Pipeline without interactive prompts | 02, 05, 06, 07 with stdin closed and no TTY; unit test `test_pipeline_does_not_read_stdin` holds stdin open and fails on the old runner |
| 10 | Compare with the existing implementation | 01, 02, 04 against the old engine (`dc04629`) |

Deliberate failures were detected and reported in 04, 05 and 06 with expected and observed
values read from the framework output (`100` vs `108`; `"Code rejected."` vs
`"That code is not valid."`), screenshots, Playwright traces and a re-run command for the
single test. The re-run commands were checked by hand to select exactly that test.
