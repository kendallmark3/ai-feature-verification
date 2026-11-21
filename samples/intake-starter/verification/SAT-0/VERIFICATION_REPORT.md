# Verification Report · SAT-0

**Client submits a project intake**

## Verdict: INCOMPLETE

- 2 test file(s) still @ai-proposed (Gate 2 open)
- Evidence is from interactive mode; re-run in pipeline mode before approval

Run `20261121T164454Z` · mode **interactive** · environment **local** · commit `ce7a1f0` (with uncommitted changes)

Tests: **6 passed · 0 failed · 0 skipped**

## Gates

- Gate 1 · Clarify (exception-based): **all questions answered**
- Gate 2 · Promote tests: **open (2 file(s))**
- Gate 3 · Human approval: **pending human decision**

## Coverage vs acceptance criteria

| AC | Result | Evidence | Criterion | Clarified as | Passed / ran |
|---|---|---|---|---|---|
| AC-1 | **PASS** | unreviewed | POST /api/intakes with a client name, a project type (ECOMMERCE, WEBSITE or API) and a description of at least 20 characters returns 201 with a reference like INT-1001 and status RECEIVED | Reference format: 'INT-' then digits (INT-1001 is the first). All three project types accepted. | 1/1 |
| AC-2 | **PASS** | unreviewed | A description shorter than 20 characters returns 400 with the error "Describe what you want in at least 20 characters" | Under 20 = 19 or fewer characters after trimming; exactly 20 is accepted. | 1/1 |
| AC-3 | **PASS** | unreviewed | GET /api/intakes/{reference} returns the submitted intake, and an unknown reference returns 404 | — | 1/1 |
| AC-4 | **PASS** | unreviewed | On the intake page, submitting a valid form shows "Your reference is INT-" followed by the number | — | 1/1 |
| AC-5 | **PASS** | unreviewed | On the intake page, a description shorter than 20 characters shows the error message and keeps what the client typed | 'Keeps what the client typed' = name, type and description fields still hold the entered values after the error. | 1/1 |

Evidence: *reviewed* = only promoted tests; *unreviewed* = AI-proposed or origin unknown; *mixed* = both. Unreviewed evidence never satisfies the pipeline requirement for VERIFIED.

## Evidence by criterion

### AC-1 · PASS
- PASS · [maven-surefire:backend · unpromoted] SAT-0 AC-1 valid intake returns 201 with an INT- reference and status RECEIVED

### AC-2 · PASS
- PASS · [maven-surefire:backend · unpromoted] SAT-0 AC-2 description under 20 characters returns 400 with the message

### AC-3 · PASS
- PASS · [maven-surefire:backend · unpromoted] SAT-0 AC-3 a submitted intake reads back by reference and an unknown one is 404

### AC-4 · PASS
- PASS · [playwright:frontend/desktop · unpromoted] SAT-0 AC-4 a valid intake shows its reference number
  - screenshot: `verification/SAT-0/runs/20261121T164454Z/playwright:frontend/artifacts/reports/e2e-artifacts/intake-SAT-0-AC-4-a-valid-intake-shows-its-reference-number-desktop/test-finished-1.png`

### AC-5 · PASS
- PASS · [playwright:frontend/desktop · unpromoted] SAT-0 AC-5 a short description shows the error and keeps what was typed
  - screenshot: `verification/SAT-0/runs/20261121T164454Z/playwright:frontend/artifacts/reports/e2e-artifacts/intake-SAT-0-AC-5-a-short--1f27b-or-and-keeps-what-was-typed-desktop/test-finished-1.png`

## Existing regression tests (untagged)

1/1 passed.

## Suites

- **maven-surefire:backend**: exit 0, 4 test case(s), log `verification/SAT-0/runs/20261121T164454Z/maven-surefire:backend.log`
- **playwright:frontend**: exit 0, 2 test case(s), log `verification/SAT-0/runs/20261121T164454Z/playwright:frontend.log`

## Working tree

Uncommitted changes at run time: 41 path(s).

---

Gate 3 is a human decision. Record it with:

`python3 "${CLAUDE_PLUGIN_ROOT}/skills/verify-feature/scripts/verify.py" approve SAT-0 --by "<your name>" --decision approved|rejected --note "..."`
