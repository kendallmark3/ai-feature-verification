# Verification Report · SHOP-142

**Discount codes at checkout**

## Verdict: INCOMPLETE

- Gate 1 has 1 open question(s); unresolved criteria: AC-2 (Q-AI-4)
- Not verifiable as written: AC-4
- 2 test file(s) still @ai-proposed (Gate 2 open)
- Evidence is from interactive mode; re-run in pipeline mode before approval

Run `20261120T051210Z` · mode **interactive** · environment **local** · commit `0e8e357`

Tests: **21 passed · 0 failed · 2 skipped**

## Gates

- Gate 1 · Clarify (exception-based): **1 open question(s)**
- Gate 2 · Promote tests: **open (2 file(s))**
- Gate 3 · Human approval: **pending human decision**

## Coverage vs acceptance criteria

| AC | Result | Evidence | Criterion | Clarified as | Passed / ran |
|---|---|---|---|---|---|
| AC-1 | **PASS** | unreviewed | User can enter a discount code in the cart | — | 2/2 |
| AC-2 | **UNRESOLVED** | unreviewed | Valid codes apply the discount to the total | Valid codes are SAVE10 (10% off) and FLAT20 ($20 off, only when subtotal >= $50, otherwise refused with 'This code needs a subtotal of at least $50.'). On the $120 cart: SAVE10 -> $108.00, FLAT20 -> $100.00. One code at a time: a second code replaces the first. Showing the discount line and new total in the cart is enough; reload/checkout out of scope. Expiry not checked for this story; letter case is accepted risk and not tested. (Q-1, Q-6, Q-AI-1, Q-AI-2, Q-AI-3, Q-AI-4, Q-AI-6) | 5/5 |
| AC-3 | **PASS** | unreviewed | Invalid codes show an error | Empty code shows exactly 'Enter a discount code.'; unknown code shows exactly 'That code is not valid.'; the total stays $120.00. A bad code entered after SAVE10 removes the SAVE10 discount. (Q-2, Q-AI-5) | 8/8 |
| AC-4 | **NOT VERIFIABLE** | — | Should be fast | Product owner recorded accepted risk at Gate 1 (Q-3): no speed threshold was set, so there is no pass/fail line to test against. | 0/0 |
| AC-5 | **PASS** | unreviewed | Works on mobile | On a Pixel 7 (Chrome) a shopper can enter a code, apply it, see the new total and see errors, with no sideways scrolling. (Q-4, Q-5) | 2/2 |

Evidence: *reviewed* = only promoted tests; *unreviewed* = AI-proposed or origin unknown; *mixed* = both. Unreviewed evidence never satisfies the pipeline requirement for VERIFIED.

## Open questions (testing continued)

| Question | Criteria | Topic | Owner |
|---|---|---|---|
| Q-AI-4 | AC-2 | AC-2 · Several codes | Product owner (not named on the story) |

Unanswered questions are never treated as approval. Affected criteria stay UNRESOLVED.

## Evidence by criterion

### AC-1 · PASS
- PASS · [e2e/desktop · unpromoted] SHOP-142 AC-1 the cart has a discount code field and Apply button
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-1-the-d3971-code-field-and-Apply-button-desktop/test-finished-1.png`
- PASS · [e2e/mobile · unpromoted] SHOP-142 AC-1 the cart has a discount code field and Apply button
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-1-the-d3971-code-field-and-Apply-button-mobile/test-finished-1.png`

### AC-2 · UNRESOLVED
- Waiting on: Q-AI-4. Not reported as passing until answered.
- PASS · [api · origin unknown] SHOP-142 AC-2 SAVE10 takes 10% off the $120 cart, total 108
- PASS · [api · origin unknown] SHOP-142 AC-2 FLAT20 takes $20 off the $120 cart, total 100
- PASS · [api · origin unknown] SHOP-142 AC-2 FLAT20 is refused below a $50 subtotal and applies at exactly $50
- PASS · [e2e/desktop · unpromoted] SHOP-142 AC-2 SAVE10 shows the discount line and total $108.00; FLAT20 then replaces it
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-2-SAV-58c17--00-FLAT20-then-replaces-it-desktop/test-finished-1.png`
- PASS · [e2e/mobile · unpromoted] SHOP-142 AC-2 SAVE10 shows the discount line and total $108.00; FLAT20 then replaces it
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-2-SAV-58c17--00-FLAT20-then-replaces-it-mobile/test-finished-1.png`

### AC-3 · PASS
- PASS · [api · origin unknown] SHOP-142 AC-3 an empty code is rejected with &quot;Enter a discount code.&quot;
- PASS · [api · origin unknown] SHOP-142 AC-3 an unknown code is rejected with &quot;That code is not valid.&quot;
- PASS · [e2e/desktop · unpromoted] SHOP-142 AC-3 an empty code shows "Enter a discount code." and the total stays $120.00
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-an--8576a--and-the-total-stays-120-00-desktop/test-finished-1.png`
- PASS · [e2e/desktop · unpromoted] SHOP-142 AC-3 an unknown code shows "That code is not valid." and the total stays $120.00
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-an--bdb76--and-the-total-stays-120-00-desktop/test-finished-1.png`
- PASS · [e2e/desktop · unpromoted] SHOP-142 AC-3 a bad code after SAVE10 shows the error and removes the discount
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-a-b-ad830-or-and-removes-the-discount-desktop/test-finished-1.png`
- PASS · [e2e/mobile · unpromoted] SHOP-142 AC-3 an empty code shows "Enter a discount code." and the total stays $120.00
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-an--8576a--and-the-total-stays-120-00-mobile/test-finished-1.png`
- PASS · [e2e/mobile · unpromoted] SHOP-142 AC-3 an unknown code shows "That code is not valid." and the total stays $120.00
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-an--bdb76--and-the-total-stays-120-00-mobile/test-finished-1.png`
- PASS · [e2e/mobile · unpromoted] SHOP-142 AC-3 a bad code after SAVE10 shows the error and removes the discount
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-a-b-ad830-or-and-removes-the-discount-mobile/test-finished-1.png`

### AC-4 · NOT VERIFIABLE
Reason: Product owner recorded accepted risk at Gate 1 (Q-3): no speed threshold was set, so there is no pass/fail line to test against.

### AC-5 · PASS
- SKIP · [e2e/desktop · unpromoted] SHOP-142 AC-5 on a Pixel 7 SAVE10 gives total $108.00 with no sideways scrolling
- SKIP · [e2e/desktop · unpromoted] SHOP-142 AC-5 on a Pixel 7 an unknown code shows the error with no sideways scrolling
- PASS · [e2e/mobile · unpromoted] SHOP-142 AC-5 on a Pixel 7 SAVE10 gives total $108.00 with no sideways scrolling
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-5-on--bc510--with-no-sideways-scrolling-mobile/test-finished-1.png`
- PASS · [e2e/mobile · unpromoted] SHOP-142 AC-5 on a Pixel 7 an unknown code shows the error with no sideways scrolling
  - screenshot: `verification/SHOP-142/runs/20261120T051210Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-5-on--0c5bb--with-no-sideways-scrolling-mobile/test-finished-1.png`

## Existing regression tests (untagged)

4/4 passed.

## Suites

- **api**: exit 0, 7 test case(s), log `verification/SHOP-142/runs/20261120T051210Z/api.log`
- **e2e**: exit 0, 16 test case(s), log `verification/SHOP-142/runs/20261120T051210Z/e2e.log`

---

Gate 3 is a human decision. Record it with:

`python3 .claude/skills/verify-feature/scripts/verify.py approve SHOP-142 --by "<your name>" --decision approved|rejected --note "..."`
