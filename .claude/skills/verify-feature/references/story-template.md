# A story the harness can test

The engine reads criteria from an **Acceptance Criteria** list in the story's description (or
the `ac_field` custom field). Each item becomes `AC-1`, `AC-2`, ... in order. Gate 1 turns vague
wording into questions, so write criteria that a test can pass or fail on its own.

## Template

Paste into the Jira description (Markdown or wiki markup both parse):

```
As a <who> I want <what> so that <why>.

## Acceptance Criteria
1. <Endpoint or page> <does what> -> <observable result with real values>
2. <Bad input> -> <status code and the exact message>
3. <Read-back or state check> -> <result>; <unknown/edge case> -> <result>
4. On the <page>, <action> shows "<exact text>"
5. On the <page>, <error case> shows the message and <what is kept on screen>

## Notes
Anything that is context, not a criterion (deadlines, links, design files).
```

## Rules of thumb

| Write | Not |
|---|---|
| `returns 400 with "Describe what you want in at least 20 characters"` | `shows an error` |
| `responds within 500 ms for 20 items` | `should be fast` |
| `at 390 px wide (Pixel 7) the form fits without horizontal scroll` | `works on mobile` |
| one behaviour per item | `and also ...` lists of five things |

Say which half a criterion is about (`POST /api/...` or `On the intake page ...`) so the plan
can put it in the right suite: API criteria in the Spring Boot JUnit tests, page criteria in
Playwright.

## Getting it into Jira on Saturday

Claude creates the epic and stories through the **Atlassian connector** (authorise it in
Claude's connector settings before the day). The engine itself only reads issues and posts
comments. Ask Claude, for example: "create an epic `Intent intake` in project SAT with these
stories, criteria under an Acceptance Criteria heading". Then `verify.py story SAT-1` pulls it
through the cloud adapter (`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` in the
environment). Without Jira, put the same content in `jira/SAT-1.json` (see `jira.md`); the
dress-rehearsal story `samples/intake-starter/jira/SAT-0.json` is an example.
