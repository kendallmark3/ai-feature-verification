# Verification Report · IDS-3

**Here’s our first Jira story, ready to paste into your project.  Story: Integrate AI Test Harness with Jira  Story Type: Story Priority: High Epic: AI Test Harness Labels: jira-integration, test-automation, intent-driven-engineering  User Story  As a QA en**

## Verdict: NOT VERIFIED

- Failing criteria: AC-2, AC-3, AC-4

Run `20261121T144836Z` · mode **interactive** · environment **local** · commit `76f0f23` (with uncommitted changes)

Tests: **20 passed · 4 failed · 1 skipped**

## Gates

- Gate 1 · Clarify (exception-based): **10 open question(s)**
- Gate 2 · Promote tests: **open (3 file(s))**
- Gate 3 · Human approval: **pending human decision**

## Coverage vs acceptance criteria

| AC | Result | Evidence | Criterion | Clarified as | Passed / ran |
|---|---|---|---|---|---|
| AC-1 | **UNRESOLVED** | unreviewed | The harness retrieves a real Jira story using its issue key. | Open: Q-1 | 4/4 |
| AC-2 | **FAIL** | unreviewed | Story descriptions and acceptance criteria are extracted correctly. | Open: Q-2 | 2/3 |
| AC-3 | **FAIL** | unreviewed | Missing acceptance criteria prevent test execution. | Open: Q-3 | 1/3 |
| AC-4 | **FAIL** | unreviewed | Test plans map test cases to acceptance criteria. | Open: Q-4 | 2/3 |
| AC-5 | **UNRESOLVED** | unreviewed | Jira integration tests produce deterministic results. | Open: Q-5 | 3/3 |
| AC-6 | **UNRESOLVED** | unreviewed | Verification reports distinguish passed, failed, skipped, and blocked tests. | Open: Q-6 | 3/3 |
| AC-7 | **UNRESOLVED** | unreviewed | Authorized verification results can be posted to Jira. | Open: Q-7 | 3/3 |
| AC-8 | **UNRESOLVED** | unreviewed | Existing simulated-Jira tests remain operational. | Open: Q-8 | 2/2 |

Evidence: *reviewed* = only promoted tests; *unreviewed* = AI-proposed or origin unknown; *mixed* = both. Unreviewed evidence never satisfies the pipeline requirement for VERIFIED.

## Open questions (testing continued)

| Question | Criteria | Topic | Owner |
|---|---|---|---|
| Q-1 | AC-1 | AC-1 · NO_OBSERVABLE_OUTCOME | Mark Kendall |
| Q-2 | AC-2 | AC-2 · VAGUE_TERM | Mark Kendall |
| Q-3 | AC-3 | AC-3 · NO_OBSERVABLE_OUTCOME | Mark Kendall |
| Q-4 | AC-4 | AC-4 · NO_OBSERVABLE_OUTCOME | Mark Kendall |
| Q-5 | AC-5 | AC-5 · NO_OBSERVABLE_OUTCOME | Mark Kendall |
| Q-6 | AC-6 | AC-6 · NO_OBSERVABLE_OUTCOME | Mark Kendall |
| Q-7 | AC-7 | AC-7 · NO_OBSERVABLE_OUTCOME | Mark Kendall |
| Q-8 | AC-8 | AC-8 · NO_OBSERVABLE_OUTCOME | Mark Kendall |
| Q-9 | story | STORY · NO_EXAMPLES | Mark Kendall |
| Q-AI-1 | story | STORY · SUMMARY_TRUNCATED | Mark Kendall |

Unanswered questions are never treated as approval. Affected criteria stay UNRESOLVED.

## Findings for developers

Full detail, including failure output and reproduction commands, is in `findings.json`.

### F-1 · requirement ambiguity · AC-2
- Test: [harness/vm] test_criteria_extracted_from_rest_v2_wiki_markup[IDS-3 AC-2]
- Expected: not stated in the failure output
- Observed: not stated in the failure output
- Message: `ac = 'IDS-3 AC-2' — fake_jira = <test_ids3_jira_integration.FakeJiraV2 object at 0x7f7e4a57c050>`
- Reproduce: `cd . && python3 -m pytest -k 'test_criteria_extracted_from_rest_v2_wiki_markup[IDS-3 AC-2]'`
- Revision `76f0f23 + uncommitted changes` · local · 2026-11-21T14:48:43Z

### F-2 · requirement ambiguity · AC-3
- Test: [harness/vm] test_plan_check_fails_when_the_story_has_no_criteria[IDS-3 AC-3]
- Expected: not stated in the failure output
- Observed: not stated in the failure output
- Message: `ac = 'IDS-3 AC-3', sandbox = PosixPath('/tmp/tmpbtpqu3ae') — @tag("AC-3")`
- Reproduce: `cd . && python3 -m pytest -k 'test_plan_check_fails_when_the_story_has_no_criteria[IDS-3 AC-3]'`
- Revision `76f0f23 + uncommitted changes` · local · 2026-11-21T14:48:43Z

### F-3 · requirement ambiguity · AC-3
- Test: [harness/vm] test_run_refuses_to_execute_without_criteria[IDS-3 AC-3]
- Expected: not stated in the failure output
- Observed: not stated in the failure output
- Message: `ac = 'IDS-3 AC-3', sandbox = PosixPath('/tmp/tmpzi3d3i2p') — @tag("AC-3")`
- Reproduce: `cd . && python3 -m pytest -k 'test_run_refuses_to_execute_without_criteria[IDS-3 AC-3]'`
- Revision `76f0f23 + uncommitted changes` · local · 2026-11-21T14:48:43Z

### F-4 · requirement ambiguity · AC-4
- Test: [harness/vm] test_documented_pytest_classname_tag_is_recognised[IDS-3 AC-4]
- Expected: not stated in the failure output
- Observed: not stated in the failure output
- Message: `ac = 'IDS-3 AC-4' — @tag("AC-4")`
- Reproduce: `cd . && python3 -m pytest -k 'test_documented_pytest_classname_tag_is_recognised[IDS-3 AC-4]'`
- Revision `76f0f23 + uncommitted changes` · local · 2026-11-21T14:48:43Z

## Evidence by criterion

### AC-1 · UNRESOLVED
- Waiting on: Q-1. Not reported as passing until answered.
- PASS · [harness/vm · origin unknown] test_local_adapter_returns_the_real_story_by_key[IDS-3 AC-1]
- PASS · [harness/vm · origin unknown] test_malformed_key_is_rejected_before_any_lookup[IDS-3 AC-1]
- PASS · [harness/vm · origin unknown] test_cloud_adapter_requests_the_issue_by_key_with_basic_auth[IDS-3 AC-1]
- PASS · [harness/vm · origin unknown] test_cloud_adapter_reports_an_unknown_key_as_an_error[IDS-3 AC-1]
- SKIP · [harness/vm · origin unknown] test_live_cloud_adapter_pulls_ids3_with_eight_criteria[IDS-3 AC-1 AC-2]

### AC-2 · FAIL
- Waiting on: Q-2. Not reported as passing until answered.
- SKIP · [harness/vm · origin unknown] test_live_cloud_adapter_pulls_ids3_with_eight_criteria[IDS-3 AC-1 AC-2]
- PASS · [harness/vm · origin unknown] test_eight_criteria_extracted_from_the_real_description[IDS-3 AC-2]
- PASS · [harness/vm · origin unknown] test_description_is_kept_verbatim[IDS-3 AC-2]
- FAIL · [harness/vm · origin unknown] test_criteria_extracted_from_rest_v2_wiki_markup[IDS-3 AC-2]
  - `ac = 'IDS-3 AC-2' — fake_jira = <test_ids3_jira_integration.FakeJiraV2 object at 0x7f7e4a57c050>`

### AC-3 · FAIL
- Waiting on: Q-3. Not reported as passing until answered.
- PASS · [harness/vm · origin unknown] test_gate1_flags_a_story_without_criteria[IDS-3 AC-3]
- FAIL · [harness/vm · origin unknown] test_plan_check_fails_when_the_story_has_no_criteria[IDS-3 AC-3]
  - `ac = 'IDS-3 AC-3', sandbox = PosixPath('/tmp/tmpbtpqu3ae') — @tag("AC-3")`
- FAIL · [harness/vm · origin unknown] test_run_refuses_to_execute_without_criteria[IDS-3 AC-3]
  - `ac = 'IDS-3 AC-3', sandbox = PosixPath('/tmp/tmpzi3d3i2p') — @tag("AC-3")`

### AC-4 · FAIL
- Waiting on: Q-4. Not reported as passing until answered.
- PASS · [harness/vm · origin unknown] test_the_ids3_plan_covers_every_criterion_and_validates[IDS-3 AC-4]
- PASS · [harness/vm · origin unknown] test_tagged_test_names_map_to_their_criteria[IDS-3 AC-4]
- FAIL · [harness/vm · origin unknown] test_documented_pytest_classname_tag_is_recognised[IDS-3 AC-4]
  - `ac = 'IDS-3 AC-4' — @tag("AC-4")`

### AC-5 · UNRESOLVED
- Waiting on: Q-5. Not reported as passing until answered.
- PASS · [harness/vm · origin unknown] test_pulling_the_same_story_twice_gives_identical_criteria[IDS-3 AC-5]
- PASS · [harness/vm · origin unknown] test_gate1_questions_are_identical_on_every_run[IDS-3 AC-5]
- PASS · [harness/vm · origin unknown] test_cloud_adapter_normalises_the_same_response_identically[IDS-3 AC-5]

### AC-6 · UNRESOLVED
- Waiting on: Q-6. Not reported as passing until answered.
- PASS · [harness/vm · origin unknown] test_junit_cases_are_classified_pass_fail_skip[IDS-3 AC-6]
- PASS · [harness/vm · origin unknown] test_a_guardrail_violation_marks_the_suite_blocked_not_failed[IDS-3 AC-6]
- PASS · [harness/vm · origin unknown] test_report_shows_all_four_outcomes[IDS-3 AC-6]

### AC-7 · UNRESOLVED
- Waiting on: Q-7. Not reported as passing until answered.
- PASS · [harness/vm · origin unknown] test_local_adapter_appends_the_comment_to_the_story[IDS-3 AC-7]
- PASS · [harness/vm · origin unknown] test_cloud_adapter_posts_the_comment_to_the_originating_issue[IDS-3 AC-7]
- PASS · [harness/vm · origin unknown] test_approval_without_a_named_person_is_refused[IDS-3 AC-7]

### AC-8 · UNRESOLVED
- Waiting on: Q-8. Not reported as passing until answered.
- PASS · [harness/vm · origin unknown] test_simulated_shop142_still_pulls_its_criteria[IDS-3 AC-8]
- PASS · [harness/vm · origin unknown] test_existing_engine_suite_passes[IDS-3 AC-8]

## Existing regression tests (untagged)

0/0 passed.

## Suites

- **harness**: exit 1, 25 test case(s), log `verification/IDS-3/runs/20261121T144836Z/harness.log`

## Working tree

Uncommitted changes at run time: 3 path(s).

---

Gate 3 is a human decision. Record it with:

`python3 .claude/skills/verify-feature/scripts/verify.py approve IDS-3 --by "<your name>" --decision approved|rejected --note "..."`
