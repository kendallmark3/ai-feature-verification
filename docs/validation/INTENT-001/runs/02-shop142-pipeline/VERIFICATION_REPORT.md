# Verification Report · SHOP-142

**Discount codes at checkout**

## Verdict: INCOMPLETE

- No evidence because planned tests were blocked or withheld: AC-1, AC-2, AC-3, AC-5
- Not verifiable as written: AC-4
- 2 test file(s) still @ai-proposed (Gate 2 open); withheld from this pipeline run

Run `20261120T051205Z` · mode **pipeline** · environment **local** · commit `0e8e357`

Tests: **4 passed · 0 failed · 0 skipped**

## Gates

- Gate 1 · Clarify (exception-based): **all questions answered**
- Gate 2 · Promote tests: **open (2 file(s))**
- Gate 3 · Human approval: **pending human decision**

## Coverage vs acceptance criteria

| AC | Result | Evidence | Criterion | Clarified as | Passed / ran |
|---|---|---|---|---|---|
| AC-1 | **BLOCKED** | none | User can enter a discount code in the cart | — | 0/0 |
| AC-2 | **BLOCKED** | none | Valid codes apply the discount to the total | Valid codes are SAVE10 (10% off) and FLAT20 ($20 off, only when subtotal >= $50, otherwise refused with 'This code needs a subtotal of at least $50.'). On the $120 cart: SAVE10 -> $108.00, FLAT20 -> $100.00. One code at a time: a second code replaces the first. Showing the discount line and new total in the cart is enough; reload/checkout out of scope. Expiry not checked for this story; letter case is accepted risk and not tested. (Q-1, Q-6, Q-AI-1, Q-AI-2, Q-AI-3, Q-AI-4, Q-AI-6) | 0/0 |
| AC-3 | **BLOCKED** | none | Invalid codes show an error | Empty code shows exactly 'Enter a discount code.'; unknown code shows exactly 'That code is not valid.'; the total stays $120.00. A bad code entered after SAVE10 removes the SAVE10 discount. (Q-2, Q-AI-5) | 0/0 |
| AC-4 | **NOT VERIFIABLE** | — | Should be fast | Product owner recorded accepted risk at Gate 1 (Q-3): no speed threshold was set, so there is no pass/fail line to test against. | 0/0 |
| AC-5 | **BLOCKED** | none | Works on mobile | On a Pixel 7 (Chrome) a shopper can enter a code, apply it, see the new total and see errors, with no sideways scrolling. (Q-4, Q-5) | 0/0 |

Evidence: *reviewed* = only promoted tests; *unreviewed* = AI-proposed or origin unknown; *mixed* = both. Unreviewed evidence never satisfies the pipeline requirement for VERIFIED.

## Not run

- `demo-app/tests/api/discount.test.mjs` · WITHHELD from pipeline run · unpromoted (Gate 2)
- `demo-app/tests/e2e/discount.spec.js` · WITHHELD from pipeline run · unpromoted (Gate 2)

## Evidence by criterion

### AC-1 · BLOCKED
- Tests withheld from this pipeline run, not yet promoted (Gate 2): e2e

### AC-2 · BLOCKED
- Tests withheld from this pipeline run, not yet promoted (Gate 2): api, e2e

### AC-3 · BLOCKED
- Tests withheld from this pipeline run, not yet promoted (Gate 2): api, e2e

### AC-4 · NOT VERIFIABLE
Reason: Product owner recorded accepted risk at Gate 1 (Q-3): no speed threshold was set, so there is no pass/fail line to test against.

### AC-5 · BLOCKED
- Tests withheld from this pipeline run, not yet promoted (Gate 2): e2e

## Existing regression tests (untagged)

4/4 passed.

## Suites

- **api**: exit 0, 2 test case(s), log `verification/SHOP-142/runs/20261120T051205Z/api.log`
- **e2e**: exit 0, 2 test case(s), log `verification/SHOP-142/runs/20261120T051205Z/e2e.log`

---

Gate 3 is a human decision. Record it with:

`python3 .claude/skills/verify-feature/scripts/verify.py approve SHOP-142 --by "<your name>" --decision approved|rejected --note "..."`
