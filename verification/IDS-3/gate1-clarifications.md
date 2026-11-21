# Gate 1 · Clarifications for IDS-3

**Story:** Here’s our first Jira story, ready to paste into your project.  Story: Integrate AI Test Harness with Jira  Story Type: Story Priority: High Epic: AI Test Harness Labels: jira-integration, test-automation, intent-driven-engineering  User Story  As a QA en

Testing does not wait for these answers. Each open question marks only the criterion it
names as UNRESOLVED: its tests may still run, but it can never be reported as passing until
the owner answers. An answer can be a decision, a rule, an example, or `Accepted risk: <why>`.
Questions from the deterministic rules come first; Claude adds judgement questions below
them with IDs `Q-AI-n`.

Check with: `python3 .claude/skills/verify-feature/scripts/verify.py gate1 IDS-3 --check`

## Q-1 · AC-1 · NO_OBSERVABLE_OUTCOME

> The harness retrieves a real Jira story using its issue key.

Owner: Mark Kendall

Question: What does the user or caller observe when this is met (a message, a value, a status)?

Answer: 

## Q-2 · AC-2 · VAGUE_TERM

> Story descriptions and acceptance criteria are extracted correctly.

Owner: Mark Kendall

Question: 'correctly' can't be tested as written. What exact, observable result counts as passing?

Answer: 

## Q-3 · AC-3 · NO_OBSERVABLE_OUTCOME

> Missing acceptance criteria prevent test execution.

Owner: Mark Kendall

Question: What does the user or caller observe when this is met (a message, a value, a status)?

Answer: 

## Q-4 · AC-4 · NO_OBSERVABLE_OUTCOME

> Test plans map test cases to acceptance criteria.

Owner: Mark Kendall

Question: What does the user or caller observe when this is met (a message, a value, a status)?

Answer: 

## Q-5 · AC-5 · NO_OBSERVABLE_OUTCOME

> Jira integration tests produce deterministic results.

Owner: Mark Kendall

Question: What does the user or caller observe when this is met (a message, a value, a status)?

Answer: 

## Q-6 · AC-6 · NO_OBSERVABLE_OUTCOME

> Verification reports distinguish passed, failed, skipped, and blocked tests.

Owner: Mark Kendall

Question: What does the user or caller observe when this is met (a message, a value, a status)?

Answer: 

## Q-7 · AC-7 · NO_OBSERVABLE_OUTCOME

> Authorized verification results can be posted to Jira.

Owner: Mark Kendall

Question: What does the user or caller observe when this is met (a message, a value, a status)?

Answer: 

## Q-8 · AC-8 · NO_OBSERVABLE_OUTCOME

> Existing simulated-Jira tests remain operational.

Owner: Mark Kendall

Question: What does the user or caller observe when this is met (a message, a value, a status)?

Answer: 

## Q-9 · STORY · NO_EXAMPLES

Owner: Mark Kendall

Question: No criterion has a concrete value or example. Can you give at least one worked example?

Answer: 

<!-- Claude: add judgement questions below this line as ## Q-AI-n · AC-x · TOPIC -->

## Q-AI-1 · STORY · SUMMARY_TRUNCATED

> Summary is 255 characters and ends mid-word ("As a QA en").

Owner: Mark Kendall

Question: The story text was pasted into Summary and cut at Jira's 255-character limit. Shorten Summary to "Integrate AI Test Harness with Jira" and move the user story into Description?

Answer: 
