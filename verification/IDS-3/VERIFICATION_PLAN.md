# Verification Plan · IDS-3

**Story:** Integrate AI Test Harness with Jira (summary field truncated in Jira, see Q-AI-1)

**Gate 1 (clarifications):** 9 open question(s). Unresolved criteria: AC-1 (Q-1), AC-2 (Q-2), AC-3 (Q-3), AC-4 (Q-4), AC-5 (Q-5), AC-6 (Q-6), AC-7 (Q-7), AC-8 (Q-8). Testing continues for every other criterion.

**Tagging rule:** pytest parametrize id 'IDS-3 AC-n' on every test in tests/ids3/

| AC | Criterion (as written) | Clarified as | Disposition | Checks |
|---|---|---|---|---|
| AC-1 | The harness retrieves a real Jira story using its issue key. | — | verify | `AC-1.a` [harness] local adapter returns IDS-3 by key; malformed key rejected; cloud adapter GETs /rest/api/2/issue/IDS-3 with Basic auth; unknown key → error<br>`AC-1.b` [harness] LIVE: cloud adapter pulls IDS-3 from intentdrivenengineering.atlassian.net (skipped unless JIRA_* set) |
| AC-2 | Story descriptions and acceptance criteria are extracted correctly. | — | verify | `AC-2.a` [harness] 8 criteria extracted from the real Description, texts exact; description kept verbatim; same from REST v2 wiki markup |
| AC-3 | Missing acceptance criteria prevent test execution. | — | verify | `AC-3.a` [harness] Gate 1 flags NO_ACCEPTANCE_CRITERIA; plan --check fails with zero ACs; run refuses to execute suites with zero ACs |
| AC-4 | Test plans map test cases to acceptance criteria. | — | verify | `AC-4.a` [harness] IDS-3 plan lists AC-1..AC-8 and validates; tagged test names map to ACs; documented pytest classname tag recognised |
| AC-5 | Jira integration tests produce deterministic results. | — | verify | `AC-5.a` [harness] same snapshot → identical ACs and Gate 1 questions; same REST response → identical normalised issue |
| AC-6 | Verification reports distinguish passed, failed, skipped, and blocked tests. | — | verify | `AC-6.a` [harness] JUnit pass/fail/skip/error classified; guardrail breach → BLOCKED suite; report lists all four outcomes |
| AC-7 | Authorized verification results can be posted to Jira. | — | verify | `AC-7.a` [harness] local adapter appends comment; cloud adapter POSTs to /rest/api/2/issue/IDS-3/comment; approve without --by refused |
| AC-8 | Existing simulated-Jira tests remain operational. | — | verify | `AC-8.a` [harness] SHOP-142 simulated story still yields its committed criteria; existing engine unit suite passes |

## Expected evidence

- `AC-1.a`: junit: harness · request path and auth header seen by REST stand-in
- `AC-1.b`: junit: harness (skip reason recorded when no credentials)
- `AC-2.a`: junit: harness · extracted AC texts
- `AC-3.a`: junit: harness · exit code and suite-ran marker
- `AC-4.a`: junit: harness
- `AC-5.a`: junit: harness
- `AC-6.a`: junit: harness
- `AC-7.a`: junit: harness · POST path and body seen by REST stand-in · live MCP comment ID once authorised
- `AC-8.a`: junit: harness · unittest exit code
