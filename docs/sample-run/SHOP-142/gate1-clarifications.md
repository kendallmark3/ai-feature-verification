# Gate 1 · Clarifications for SHOP-142

**Story:** Discount codes at checkout

Every question needs an `Answer:` before Gate 1 passes. An answer can be a decision,
a rule, an example, or `Accepted risk: <why>`. Questions from the deterministic rules come
first; Claude adds judgement questions below them with IDs `Q-AI-n`.

Check with: `python3 .claude/skills/verify-feature/scripts/verify.py gate1 SHOP-142 --check`

## Q-1 · AC-2 · UNDEFINED_RULE

> Valid codes apply the discount to the total

Question: What makes something 'valid'? List the rules or give concrete examples of each case.

Answer: (simulated PO) SAVE10 = 10% off. FLAT20 = $20 off orders of $50 or more. Only codes on the promo list that have not expired.

## Q-2 · AC-3 · UNDEFINED_RULE

> Invalid codes show an error

Question: What makes something 'invalid'? List the rules or give concrete examples of each case.

Answer: (simulated PO) Unknown codes, expired codes, and FLAT20 under $50. Show a message under the field and leave the total unchanged.

## Q-3 · AC-4 · UNMEASURED_NFR

> Should be fast

Question: 'fast' has no number. What threshold, measured where (API, page load, click-to-result), at what percentile, under what load?

Answer: (simulated PO) Accepted risk: we don't have a number yet. Marketing just doesn't want it to feel slow. Revisit after launch.

## Q-4 · AC-5 · VAGUE_TERM

> Works on mobile

Question: 'works' can't be tested as written. What exact, observable result counts as passing?

Answer: (simulated PO) On a phone the shopper can enter a code, apply it and see the new total without zooming or scrolling sideways.

## Q-5 · AC-5 · UNSPECIFIED_ENVIRONMENT

> Works on mobile

Question: 'mobile' — which devices, browsers or viewport widths must pass?

Answer: (simulated PO) Current iPhone and Android phones. Testing on a Pixel-size screen is fine.

## Q-6 · STORY · NO_EXAMPLES

Question: No criterion has a concrete value or example. Can you give at least one worked example?

Answer: (simulated PO) $120 cart: SAVE10 takes $12.00 off, total $108.00. FLAT20 takes $20.00 off, total $100.00.

<!-- Claude: add judgement questions below this line as ## Q-AI-n · AC-x · TOPIC -->

## Q-AI-1 · AC-2 · Expired codes

Question: Every code in `demo-app/server/discounts.js` has an `expires` date (WELCOME5 ended 2025-06-30), but the story never mentions expiry. Should an expired code be rejected, and with what message?

Answer: (simulated PO) Yes, reject expired codes with an error like invalid ones. WELCOME5 must not work any more.

## Q-AI-2 · AC-2 · Upper/lower case

Question: Codes are looked up exactly as typed (`CODES[raw]`), so `save10` is refused. Should codes be case-insensitive?

Answer: (simulated PO) Not case-sensitive. People type save10, Save10, whatever.

## Q-AI-3 · AC-2 · Minimum order for FLAT20

Question: FLAT20 has `minSubtotal: 50` in the code. Is a $50 minimum the rule, and should the message say the minimum?

Answer: (simulated PO) Yes, $50 minimum, and the message should say $50.

## Q-AI-4 · AC-2 · More than one code

Question: What happens if a shopper applies a second code — replace the first, stack, or refuse?

Answer: (simulated PO) One code at a time. A new code replaces the old one.

