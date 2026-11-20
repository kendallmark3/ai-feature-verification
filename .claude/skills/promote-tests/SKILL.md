---
name: promote-tests
description: Gate 2 of feature verification. Prepare AI-proposed tests for human review so they can be promoted into the committed regression suite and run in pipeline mode. Use when tests are marked @ai-proposed, when asked to review or promote generated tests, or as step 7 of verify-feature.
---

# Promote Tests (Gate 2)

Nothing AI-generated reaches CI unreviewed. A test file stays marked `@ai-proposed` until a
person reads it and promotes it; pipeline mode refuses to run while any marker remains.

```bash
V=.claude/skills/verify-feature/scripts/verify.py
```

1. `python3 $V proposed` lists every file still marked `@ai-proposed`.
2. For each file, write the reviewer a short brief, one block per test:
   - which AC it verifies and the clarified rule it encodes
   - what it asserts, in one line of plain language
   - its result in the latest interactive run (from `verification/<KEY>/evidence.json`)
3. Check each test against this list and say what you find, good or bad:
   - asserts an observable outcome, not an implementation detail
   - no fixed sleeps, no reliance on test order, no shared mutable state, no real clock
     unless the rule is about time (then pin the date)
   - stable selectors (role, label, test id), no brittle CSS paths
   - data it needs is created by the test or a fixture, not assumed to exist
   - a failing test still asserts the clarified intent: it was not loosened to pass
   - no product code was changed to make it pass
4. Suggest the review route the team uses: a pull request with only the test files and
   `verification/<KEY>/` is the usual one.
5. Promotion is the person's act. They run:

   ```bash
   python3 $V promote <file> --by "<their name>" --story <KEY>
   ```

   which replaces the marker with `@approved-by <name> <date>` and logs it in
   `verification/<KEY>/gate2-promotions.json`. Run it yourself only when the person tells you
   to in this conversation and gives their name. If they want changes, make them, keep the
   marker, and go round again.
6. When `proposed` returns an empty list, Gate 2 has passed. Continue with the pipeline run.
