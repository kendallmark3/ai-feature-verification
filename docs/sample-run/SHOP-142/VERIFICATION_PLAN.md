# Verification Plan · SHOP-142

**Story:** Discount codes at checkout

**Gate 1 (clarifications):** passed

**Tagging rule:** Every test that verifies a criterion names it in its title, e.g. 'SHOP-142 AC-1 ...'

| AC | Criterion (as written) | Clarified as | Disposition | Checks |
|---|---|---|---|---|
| AC-1 | User can enter a discount code in the cart | The cart page has a labelled 'Discount code' field and an Apply button. | verify | `AC-1.a` [e2e] Cart page shows a labelled Discount code input and an Apply button |
| AC-2 | Valid codes apply the discount to the total | SAVE10 = 10% off; FLAT20 = $20 off orders of $50+. Case-insensitive. One code at a time; a new code replaces the old. $120 cart: SAVE10 → $108.00, FLAT20 → $100.00. (Q-1, Q-6, Q-AI-2, Q-AI-3, Q-AI-4) | verify | `AC-2.a` [api] API: SAVE10 and FLAT20 return the right discount and total for a $120 cart<br>`AC-2.b` [api] API: lower-case save10 is accepted<br>`AC-2.c` [e2e] UI: applying SAVE10 shows the discount line and total $108.00; applying FLAT20 next replaces it with total $100.00 |
| AC-3 | Invalid codes show an error | Unknown codes, expired codes (WELCOME5) and FLAT20 under $50 are refused with a message under the field; total unchanged. FLAT20 message states $50. (Q-2, Q-AI-1, Q-AI-3) | verify | `AC-3.a` [api] API: unknown and expired codes return 400 with an error message<br>`AC-3.b` [api] API: FLAT20 under $50 is refused with a message that names $50 (rule tested directly against discount logic)<br>`AC-3.c` [e2e] UI: an unknown code shows an alert and the total stays $120.00 |
| AC-4 | Should be fast | — | not-verifiable | No threshold agreed. PO recorded accepted risk (Q-3): 'Revisit after launch.' Without a number there is no pass/fail. |
| AC-5 | Works on mobile | On a Pixel-size phone the shopper can enter a code, apply it and see the new total with no sideways scrolling. (Q-4, Q-5) | verify | `AC-5.a` [e2e] Mobile project: apply SAVE10 and see $108.00; page has no horizontal overflow |

## Expected evidence

- `AC-1.a`: junit: e2e (desktop + mobile), screenshot
- `AC-2.a`: junit: api, response values
- `AC-2.b`: junit: api
- `AC-2.c`: junit: e2e, screenshot
- `AC-3.a`: junit: api, status code + error body
- `AC-3.b`: junit: api
- `AC-3.c`: junit: e2e, screenshot
- `AC-5.a`: junit: e2e/mobile, screenshot
