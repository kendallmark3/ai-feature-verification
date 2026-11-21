# Verification Report · IDS-3

**Here’s our first Jira story, ready to paste into your project.  Story: Integrate AI Test Harness with Jira  Story Type: Story Priority: High Epic: AI Test Harness Labels: jira-integration, test-automation, intent-driven-engineering  User Story  As a QA en**

## Verdict: INCOMPLETE

- Gate 1 has 10 open question(s); unresolved criteria: AC-1 (Q-1), AC-2 (Q-2), AC-3 (Q-3), AC-4 (Q-4), AC-5 (Q-5), AC-6 (Q-6), AC-7 (Q-7), AC-8 (Q-8); story-level: Q-9, Q-AI-1
- 3 test file(s) still @ai-proposed (Gate 2 open)
- Evidence is from interactive mode; re-run in pipeline mode before approval

Run `20261121T161053Z` · mode **interactive** · environment **local** · commit `ff9196d` (with uncommitted changes)

Tests: **25 passed · 0 failed · 0 skipped**

## Gates

- Gate 1 · Clarify (exception-based): **10 open question(s)**
- Gate 2 · Promote tests: **open (3 file(s))**
- Gate 3 · Human approval: **pending human decision**

## Coverage vs acceptance criteria

| AC | Result | Evidence | Criterion | Clarified as | Passed / ran |
|---|---|---|---|---|---|
| AC-1 | **UNRESOLVED** | unreviewed | The harness retrieves a real Jira story using its issue key. | Open: Q-1 | 5/5 |
| AC-2 | **UNRESOLVED** | unreviewed | Story descriptions and acceptance criteria are extracted correctly. | Open: Q-2 | 4/4 |
| AC-3 | **UNRESOLVED** | unreviewed | Missing acceptance criteria prevent test execution. | Open: Q-3 | 3/3 |
| AC-4 | **UNRESOLVED** | unreviewed | Test plans map test cases to acceptance criteria. | Open: Q-4 | 3/3 |
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

## Evidence by criterion

### AC-1 · UNRESOLVED
- Waiting on: Q-1. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_cloud_adapter_reports_an_unknown_key_as_an_error
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_cloud_adapter_requests_the_issue_by_key_with_basic_auth
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_local_adapter_returns_the_real_story_by_key
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_malformed_key_is_rejected_before_any_lookup
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_live_cloud_adapter_pulls_ids3_with_eight_criteria

### AC-2 · UNRESOLVED
- Waiting on: Q-2. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_live_cloud_adapter_pulls_ids3_with_eight_criteria
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_criteria_extracted_from_rest_v2_wiki_markup
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_description_is_kept_verbatim
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_eight_criteria_extracted_from_the_real_description

### AC-3 · UNRESOLVED
- Waiting on: Q-3. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_gate1_flags_a_story_without_criteria
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_plan_check_fails_when_the_story_has_no_criteria
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_run_refuses_to_execute_without_criteria

### AC-4 · UNRESOLVED
- Waiting on: Q-4. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_documented_class_name_tag_is_recognised
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_tagged_test_names_map_to_their_criteria
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_the_ids3_plan_covers_every_criterion_and_validates

### AC-5 · UNRESOLVED
- Waiting on: Q-5. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_cloud_adapter_normalises_the_same_response_identically
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_gate1_questions_are_identical_on_every_run
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_pulling_the_same_story_twice_gives_identical_criteria

### AC-6 · UNRESOLVED
- Waiting on: Q-6. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_a_guardrail_violation_marks_the_suite_blocked_not_failed
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_junit_cases_are_classified_pass_fail_skip
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_report_shows_all_four_outcomes

### AC-7 · UNRESOLVED
- Waiting on: Q-7. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_approval_without_a_named_person_is_refused
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_cloud_adapter_posts_the_comment_to_the_originating_issue
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_local_adapter_appends_the_comment_to_the_story

### AC-8 · UNRESOLVED
- Waiting on: Q-8. Not reported as passing until answered.
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_existing_engine_suite_passes
- PASS · [harness/marks-MacBook-Air.local · origin unknown] test_simulated_shop142_still_pulls_its_criteria

## Existing regression tests (untagged)

0/0 passed.

## Suites

- **harness**: exit 0, 25 test case(s), log `verification/IDS-3/runs/20261121T161053Z/harness.log`

## Working tree

Uncommitted changes at run time: 1 path(s).

---

Gate 3 is a human decision. Record it with:

`python3 .claude/skills/verify-feature/scripts/verify.py approve IDS-3 --by "<your name>" --decision approved|rejected --note "..."`
