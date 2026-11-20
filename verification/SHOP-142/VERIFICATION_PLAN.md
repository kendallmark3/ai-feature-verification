# Verification Plan · SHOP-142

**Story:** Discount codes at checkout

**Gate 1 (clarifications):** passed

**Tagging rule:** Every test that verifies a criterion names it in its title, e.g. 'SHOP-142 AC-1 ...'

| AC | Criterion (as written) | Clarified as | Disposition | Checks |
|---|---|---|---|---|
| AC-1 | User can enter a discount code in the cart | — | verify | `AC-1.a` [e2e] Cart page has a labelled 'Discount code' input and an Apply button; a typed code is kept in the input |
| AC-2 | Valid codes apply the discount to the total | Valid codes are SAVE10 (10% off) and FLAT20 ($20 off, only when subtotal >= $50, otherwise refused with 'This code needs a subtotal of at least $50.'). On the $120 cart: SAVE10 -> $108.00, FLAT20 -> $100.00. One code at a time: a second code replaces the first. Showing the discount line and new total in the cart is enough; reload/checkout out of scope. Expiry not checked for this story; letter case is accepted risk and not tested. (Q-1, Q-6, Q-AI-1, Q-AI-2, Q-AI-3, Q-AI-4, Q-AI-6) | verify | `AC-2.a` [api] POST /api/cart/discount with SAVE10 returns discount 12 and total 108; with FLAT20 returns discount 20 and total 100<br>`AC-2.b` [api] FLAT20 below a $50 subtotal is refused with 'This code needs a subtotal of at least $50.'; at exactly $50 it applies (discount rules called directly, since the demo cart is fixed at $120)<br>`AC-2.c` [e2e] In the browser, applying SAVE10 shows 'Discount (SAVE10) −$12.00' and Total $108.00; then applying FLAT20 replaces it with −$20.00 and Total $100.00 |
| AC-3 | Invalid codes show an error | Empty code shows exactly 'Enter a discount code.'; unknown code shows exactly 'That code is not valid.'; the total stays $120.00. A bad code entered after SAVE10 removes the SAVE10 discount. (Q-2, Q-AI-5) | verify | `AC-3.a` [api] API returns 400 with the exact error text for an empty code and an unknown code<br>`AC-3.b` [e2e] In the browser, empty and unknown codes show the exact error in an alert and Total stays $120.00<br>`AC-3.c` [e2e] After SAVE10 is applied, an unknown code shows the error, removes the discount line and Total returns to $120.00 |
| AC-4 | Should be fast | — | not-verifiable | Product owner recorded accepted risk at Gate 1 (Q-3): no speed threshold was set, so there is no pass/fail line to test against. |
| AC-5 | Works on mobile | On a Pixel 7 (Chrome) a shopper can enter a code, apply it, see the new total and see errors, with no sideways scrolling. (Q-4, Q-5) | verify | `AC-5.a` [e2e] Playwright 'mobile' project (Pixel 7): apply SAVE10 -> Total $108.00, page has no horizontal overflow<br>`AC-5.b` [e2e] Playwright 'mobile' project (Pixel 7): unknown code shows 'That code is not valid.', no horizontal overflow |

## Expected evidence

- `AC-1.a`: junit: e2e (desktop + mobile), screenshot
- `AC-2.a`: junit: api, response body values
- `AC-2.b`: junit: api
- `AC-2.c`: junit: e2e, screenshot
- `AC-3.a`: junit: api, response body values
- `AC-3.b`: junit: e2e, screenshot
- `AC-3.c`: junit: e2e, screenshot
- `AC-5.a`: junit: e2e (mobile), screenshot
- `AC-5.b`: junit: e2e (mobile), screenshot
