# Triage: test bug or product defect?

For every failing tagged test, decide which it is before reporting.

**Test bug** — the test is wrong about how to observe the behaviour:
wrong selector, wrong URL or port, missing wait for a network response, wrong fixture,
asserting formatting the plan didn't require. Fix the test, keep the marker, re-run.

**Product defect** — the test correctly encodes the clarified rule and the product does
something else. Don't touch product code (unless the person asks you to fix it as a
separate task). Report it:

- AC and the clarified rule (quote the Gate 1 answer)
- the exact request or steps, the expected and the actual result
- the evidence: test name, log path, screenshot path
- where in the code the behaviour comes from, if you can see it

**Ambiguous** — the test and the product follow two readings of the rule. That's a Gate 1
miss: add a `Q-AI-n` question, mark the AC `not-verifiable` until it's answered, and say so.

Never change an assertion so that a failing test passes unless the clarified rule says the
current behaviour is correct.
