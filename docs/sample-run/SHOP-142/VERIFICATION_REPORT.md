# Verification Report · SHOP-142

**Discount codes at checkout**

## Verdict: NOT VERIFIED

- Failing criteria: AC-2, AC-3

Run `20261119T234555Z` · mode **pipeline** · environment **local**

## Gates

- Gate 1 · Clarify: **passed**
- Gate 2 · Promote tests: **passed**
- Gate 3 · Human approval: **pending human decision**

## Coverage vs acceptance criteria

| AC | Result | Criterion | Clarified as | Passed / ran |
|---|---|---|---|---|
| AC-1 | **PASS** | User can enter a discount code in the cart | The cart page has a labelled 'Discount code' field and an Apply button. | 2/2 |
| AC-2 | **FAIL** | Valid codes apply the discount to the total | SAVE10 = 10% off; FLAT20 = $20 off orders of $50+. Case-insensitive. One code at a time; a new code replaces the old. $120 cart: SAVE10 → $108.00, FLAT20 → $100.00. (Q-1, Q-6, Q-AI-2, Q-AI-3, Q-AI-4) | 4/5 |
| AC-3 | **FAIL** | Invalid codes show an error | Unknown codes, expired codes (WELCOME5) and FLAT20 under $50 are refused with a message under the field; total unchanged. FLAT20 message states $50. (Q-2, Q-AI-1, Q-AI-3) | 4/5 |
| AC-4 | **NOT VERIFIABLE** | Should be fast | No threshold agreed. PO recorded accepted risk (Q-3): 'Revisit after launch.' Without a number there is no pass/fail. | 0/0 |
| AC-5 | **PASS** | Works on mobile | On a Pixel-size phone the shopper can enter a code, apply it and see the new total with no sideways scrolling. (Q-4, Q-5) | 1/1 |

## Evidence by criterion

### AC-1 · PASS
- PASS · [e2e/desktop] SHOP-142 AC-1 cart page has a labelled discount code field and an Apply button
  - screenshot: `verification/SHOP-142/runs/20261119T234555Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-1-car-7c203-e-field-and-an-Apply-button-desktop/test-finished-1.png`
- PASS · [e2e/mobile] SHOP-142 AC-1 cart page has a labelled discount code field and an Apply button
  - screenshot: `verification/SHOP-142/runs/20261119T234555Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-1-car-7c203-e-field-and-an-Apply-button-mobile/test-finished-1.png`

### AC-2 · FAIL
- PASS · [api] SHOP-142 AC-2 SAVE10 takes 10% off a $120 cart (total 108.00)
- PASS · [api] SHOP-142 AC-2 FLAT20 takes $20 off a $120 cart (total 100.00)
- FAIL · [api] SHOP-142 AC-2 codes are not case-sensitive (save10 is accepted)
  - `lower-case save10 should be accepted — 400 !== 200`
- PASS · [e2e/desktop] SHOP-142 AC-2 SAVE10 shows the discount and a $108.00 total; FLAT20 then replaces it ($100.00)
  - screenshot: `verification/SHOP-142/runs/20261119T234555Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-2-SAV-32b87-20-then-replaces-it-100-00--desktop/test-finished-1.png`
- PASS · [e2e/mobile] SHOP-142 AC-2 SAVE10 shows the discount and a $108.00 total; FLAT20 then replaces it ($100.00)
  - screenshot: `verification/SHOP-142/runs/20261119T234555Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-2-SAV-32b87-20-then-replaces-it-100-00--mobile/test-finished-1.png`

### AC-3 · FAIL
- PASS · [api] SHOP-142 AC-3 an unknown code is refused with a message
- FAIL · [api] SHOP-142 AC-3 an expired code (WELCOME5) is refused with a message
  - `WELCOME5 expired on 2025-06-30 and must be refused — 200 !== 400`
- PASS · [api] SHOP-142 AC-3 FLAT20 under $50 is refused and the message names $50
- PASS · [e2e/desktop] SHOP-142 AC-3 an unknown code shows an error and leaves the total at $120.00
  - screenshot: `verification/SHOP-142/runs/20261119T234555Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-an--4a587--leaves-the-total-at-120-00-desktop/test-finished-1.png`
- PASS · [e2e/mobile] SHOP-142 AC-3 an unknown code shows an error and leaves the total at $120.00
  - screenshot: `verification/SHOP-142/runs/20261119T234555Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-3-an--4a587--leaves-the-total-at-120-00-mobile/test-finished-1.png`

### AC-4 · NOT VERIFIABLE
Reason: No threshold agreed. PO recorded accepted risk (Q-3): 'Revisit after launch.' Without a number there is no pass/fail.

### AC-5 · PASS
- SKIP · [e2e/desktop] SHOP-142 AC-5 on a phone the shopper applies SAVE10 and sees $108.00 without sideways scrolling
- PASS · [e2e/mobile] SHOP-142 AC-5 on a phone the shopper applies SAVE10 and sees $108.00 without sideways scrolling
  - screenshot: `verification/SHOP-142/runs/20261119T234555Z/e2e/artifacts/reports/e2e-artifacts/discount-SHOP-142-AC-5-on--df49f--without-sideways-scrolling-mobile/test-finished-1.png`

## Existing regression tests (untagged)

4/4 passed.

## Suites

- **api**: exit 1, 8 test case(s), log `verification/SHOP-142/runs/20261119T234555Z/api.log`
- **e2e**: exit 0, 10 test case(s), log `verification/SHOP-142/runs/20261119T234555Z/e2e.log`

---

Gate 3 is a human decision. Record it with:

`python3 .claude/skills/verify-feature/scripts/verify.py approve SHOP-142 --by "<your name>" --decision approved|rejected --note "..."`
