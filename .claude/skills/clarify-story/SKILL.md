---
name: clarify-story
description: Gate 1 of feature verification. Find the gaps and ambiguities in a story's acceptance criteria and get them answered by a person before any test is planned or run. Use when asked whether a story or ticket is ready, testable or clear, or as step 3 of verify-feature.
---

# Clarify Story (Gate 1)

Testing an unclear criterion only proves the code does *something*. This gate makes the
person who owns the story say what "done" means before anything runs.

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
4. Show the person the questions, grouped by AC, in plain language, and ask them to answer.
   They can edit the file or answer in chat. When they answer in chat, write their words on
   the `Answer:` line; don't paraphrase them into something stronger, and never answer a
   question yourself. "Accepted risk: <why>" is a valid answer.
5. Run `python3 $V gate1 <KEY> --check`. Exit code 0 means Gate 1 passed. Anything else:
   list the open question IDs and stop.

If the person wants to skip the gate, say what will be weaker (criteria verified against a
guess), record `Accepted risk: skipped by <name>` on each open question, and continue.
