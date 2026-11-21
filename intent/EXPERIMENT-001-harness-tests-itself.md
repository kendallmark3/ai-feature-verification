# EXPERIMENT 001: The Test Harness Tests Itself

Project: Intent Driven Saturdays · Repository: ai-feature-verification

## Intent
Demonstrate that the harness can retrieve a real Jira story, generate a test plan, execute
meaningful verification against its own Jira integration, and report evidence-based results.

## Inputs
Existing repository · existing Jira Cloud account · existing Jira integration story ·
Atlassian MCP server · existing Jira REST adapter · securely configured authentication.

## Required outcomes
1. Establish authenticated Jira connectivity.
2. Retrieve the existing Jira integration story.
3. Extract its acceptance criteria.
4. Generate a traceable test plan.
5. Identify which acceptance criteria can actually be tested.
6. Execute applicable integration tests.
7. Produce deterministic results.
8. Publish an authorized test summary to Jira.

## Constraints
- Do not rebuild existing functionality or introduce unnecessary dependencies.
- Do not fabricate test results; connectivity is not proof of integration.
- Do not create Jira stories or defects; do not change workflow status.
- Do not expose credentials. Preserve the simulated Jira workflow.
- Small enough to review in a three-hour session.

## Success criteria
A real Jira story drives a verification run against the harness's own Jira integration. The
report distinguishes passed, failed, skipped and blocked tests; every executed test has
evidence; the report is associated with the originating story.

## Stop conditions
Stop if authentication fails, the story cannot be located, or the available requirements
cannot support meaningful testing. Report incomplete coverage rather than inventing success.

Principle: minimum sufficient implementation, maximum useful evidence.

Run 1 result: [verification/IDS-3/EXPERIMENT-001-REPORT.md](../verification/IDS-3/EXPERIMENT-001-REPORT.md)
