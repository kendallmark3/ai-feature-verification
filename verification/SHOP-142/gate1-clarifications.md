# Gate 1 · Clarifications for SHOP-142

**Story:** Discount codes at checkout

Every question needs an `Answer:` before Gate 1 passes. An answer can be a decision,
a rule, an example, or `Accepted risk: <why>`. Questions from the deterministic rules come
first; Claude adds judgement questions below them with IDs `Q-AI-n`.

Check with: `python3 .claude/skills/verify-feature/scripts/verify.py gate1 SHOP-142 --check`

## Q-1 · AC-2 · UNDEFINED_RULE

> Valid codes apply the discount to the total

Question: What makes something 'valid'? List the rules or give concrete examples of each case.

Answer: SAVE10 & FLAT20, as shown — those two codes are valid. On the $120 cart: SAVE10 = 10% off → $108.00; FLAT20 = $20 off → $100.00. (WELCOME5: see Q-AI-1.) _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-2 · AC-3 · UNDEFINED_RULE

> Invalid codes show an error

Question: What makes something 'invalid'? List the rules or give concrete examples of each case.

Answer: Empty + unknown, exact text — an empty code shows exactly 'Enter a discount code.', an unknown code shows exactly 'That code is not valid.', and the total stays $120.00. _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-3 · AC-4 · UNMEASURED_NFR

> Should be fast

Question: 'fast' has no number. What threshold, measured where (API, page load, click-to-result), at what percentile, under what load?

Answer: Accepted risk: product owner chose not to set a number at Gate 1; AC-4 is not verifiable. _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-4 · AC-5 · VAGUE_TERM

> Works on mobile

Question: 'works' can't be tested as written. What exact, observable result counts as passing?

Answer: Pixel 7, full flow — a shopper can enter a code, apply it, see the new total and see errors, with no sideways scrolling. _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-5 · AC-5 · UNSPECIFIED_ENVIRONMENT

> Works on mobile

Question: 'mobile' — which devices, browsers or viewport widths must pass?

Answer: Pixel 7 (Chrome). _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-6 · STORY · NO_EXAMPLES

Question: No criterion has a concrete value or example. Can you give at least one worked example?

Answer: On the $120 cart: SAVE10 → $108.00; FLAT20 → $100.00. _(product owner, Gate 1 in chat, 2026-11-19)_

<!-- Claude: add judgement questions below this line as ## Q-AI-n · AC-x · TOPIC -->

## Q-AI-1 · AC-2 · Expired codes

Question: Every code has an expiry date (`demo-app/server/discounts.js:14-16`), and WELCOME5's was 2025-06-30, but `applyDiscount` never checks it, so WELCOME5 still takes 5% off today. Should an expired code be rejected? If so, with what message?

Answer: Accept (current) — expiry dates don't matter for this story. _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-AI-2 · AC-2 · Upper/lower case and spaces

Question: Codes are matched exactly as typed, after trimming spaces (`discounts.js:26-29`), so `save10` is rejected as "That code is not valid." Should `save10` and ` SAVE10 ` work the same as `SAVE10`?

Answer: Accepted risk: product owner chose not to decide letter-case handling at Gate 1; it stays unverified. _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-AI-3 · AC-2 · Minimum subtotal

Question: FLAT20 needs a subtotal of at least $50, or it shows "This code needs a subtotal of at least $50." (`discounts.js:15, 31-33`). Is that a real business rule, and is that the message you want? (The demo cart is always $120, so this can only be checked through the API, not the page.)

Answer: Yes, keep rule + message — below a $50 subtotal FLAT20 is refused with 'This code needs a subtotal of at least $50.' (checked below the page level, since the demo cart is always $120). _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-AI-4 · AC-2 · Several codes

Question: Applying a second valid code replaces the first one; codes never add up (`demo-app/web/src/App.jsx:27`). Is one code at a time correct?

Answer: One code at a time — a second code replaces the first. _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-AI-5 · AC-3 · Invalid code after a valid one

Question: If a shopper applies SAVE10 and then types a bad code, the page shows the error and removes the SAVE10 discount (`App.jsx:23-25`). Should the earlier discount stay or go?

Answer: A bad code entered after SAVE10 removes the SAVE10 discount (matches today). _(product owner, Gate 1 in chat, 2026-11-19)_

## Q-AI-6 · AC-2 · Keeping the discount

Question: The story says "at checkout", but the discount is kept only on the page and is lost on reload; there's no checkout step in the app (`App.jsx:8`, `demo-app/server/server.js:52-58`). Must the discount survive a reload or carry into a checkout step, or is showing the new total in the cart enough?

Answer: Cart total is enough — AC-2 passes when the cart shows the discount line and new total. Reload/checkout is out of scope. _(product owner, Gate 1 in chat, 2026-11-19)_
