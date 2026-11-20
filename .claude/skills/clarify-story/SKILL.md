---
name: clarify-story
description: Gate 1 of feature verification. Find the gaps and ambiguities in a story's acceptance criteria and record each as a question for the person who owns the answer, without holding up testing of everything else. Use when asked whether a story or ticket is ready, testable or clear, or as step 3 of verify-feature.
---

# Clarify Story (Gate 1)

Testing an unclear criterion only proves the code does *something*. This gate records what
"done" still doesn't say, and who has to say it, **without stopping the rest of verification**.
Clarification is exception-based:

- An open question marks only the criteria it names as UNRESOLVED. Their tests may run, but
  they are never reported as passing, and the verdict can't be VERIFIED, until it's answered.
- Every other criterion is planned, tested and reported normally.
- An unanswered question is never treated as approval or as an implied answer.

```bash
V=.claude/skills/verify-feature/scripts/verify.py
```

1. If `verification/<KEY>/story.json` is missing, run `python3 $V story <KEY>`.
2. Run `python3 $V gaps <KEY>`. It writes `verification/<KEY>/gate1-clarifications.md` with
   questions from fixed rules (vague words, unmeasured performance, undefined "valid",
   unspecified devices, no examples, no error path). Same story, same questions, every time.
   If the file already exists, don't pass `--force` unless the person agrees: it may hold answers.
3. Add your own judgement questions. Read the story and the code it touches and ask
   what the rules can't see: business rules the code implies but the story doesn't state
   (expiry, case sensitivity, limits, stacking, rounding), roles and permissions, data that
   must already exist, behaviour that is ambiguous between two reasonable readings.
   Append each one below the marker comment in the same format:

   ```markdown
   ## Q-AI-1 · AC-2 · Expired codes

   Question: Each discount in the code has an expiry date. Should an expired code be rejected? With what message?

   Answer: 
   ```

   Ask only questions whose answer would change a test. Point to the code that raised it.
4. Write an `Owner:` line under each question you add: the person who can decide it. The
   engine fills it in for rule questions from the story's reporter. Use the story reporter
   or product owner for business rules, and name a different owner when the question is
   someone else's to decide (security, legal, a platform team).
5. Run `python3 $V gate1 <KEY> --check`. It lists open questions by criterion and owner.
   Exit 2 means questions are still open. **Continue with the plan and tests anyway**, for
   every criterion that doesn't depend on an answer. Where it does, don't write a test that
   guesses the expected behaviour: plan only what is unambiguous, or leave that AC's checks
   empty until answered.
6. Show the person the open questions, grouped by owner, in plain language, alongside the
   results, not as a blocker before them. When someone answers (in the file or in chat),
   write their words on the `Answer:` line; don't paraphrase them into something stronger,
   and never answer a question yourself. "Accepted risk: <why>" is a valid answer.
7. After answers arrive, `python3 $V report <KEY>` re-reads the file: criteria whose
   questions are answered stop being UNRESOLVED. Re-run tests if the answer changes what
   they should assert.

Only hold back an affected test when the ambiguity makes it unsafe or meaningless to run,
for example when it would write to shared data under an unknown rule. Never hold back
unrelated tests.
