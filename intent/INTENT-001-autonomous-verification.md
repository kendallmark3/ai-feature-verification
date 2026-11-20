INTENT-001: Autonomous Evidence-Based Feature Verification

Repository: kendallmark3/ai-feature-verification
Status: Ready for implementation
Priority: High
Implementation approach: Progressive Intent / Minimum Sufficient Change

1. INTENT

Evolve the existing AI Feature Verification capability from an approval-driven workflow into an autonomous, evidence-based testing workflow.

A QA engineer must be able to invoke feature verification against a Jira story and have the system execute all authorized tests without unnecessary human interaction.

The system must distinguish between:

* Executing tests.
* Identifying requirements ambiguity.
* Accepting business risk.
* Promoting tests into permanent regression suites.
* Approving feature acceptance or release.

The tester is responsible for producing evidence of application behavior, not making unauthorized product or business decisions.

Primary objective: Run the tests, collect the evidence, report the findings, and escalate only genuine exceptions.

2. EXISTING CAPABILITIES TO PRESERVE

Inspect the repository before modifying anything.

Preserve the existing capabilities wherever possible:

* Jira story retrieval and acceptance-criteria extraction.
* Test framework discovery.
* AI-assisted test planning.
* API test generation and execution.
* Playwright end-to-end testing using Chromium.
* Existing test framework integration.
* Evidence collection and reporting.
* Acceptance-criteria traceability.
* Deterministic verification rules.
* GitHub Actions execution.
* Existing skill and hook architecture.
* Current verification status semantics and exit codes, except where an explicit compatibility-preserving extension is justified.

Do not rebuild working components.

Do not introduce a new orchestration framework, service, database, or infrastructure dependency without demonstrated necessity.

3. REQUIRED BEHAVIOR

3.1 Default execution

When a tester requests:

Verify SHOP-142

The system should:

1. Retrieve the Jira story.
2. Extract its acceptance criteria.
3. Inspect the existing tests and supported frameworks.
4. Identify missing test coverage.
5. Generate an executable test plan.
6. Create temporary or isolated test cases where authorized.
7. Execute applicable API and end-to-end tests.
8. Collect screenshots, logs, and execution results.
9. Map test evidence to acceptance criteria.
10. Generate a verification report.
11. Identify defects and recommend investigation or remediation.
12. Record unresolved questions for the appropriate owner.

Normal verification must not require the tester to approve every stage.

3.2 Clarification policy

Change the existing mandatory clarification gate into an exception-based mechanism.

Ambiguous requirements must not automatically prevent unrelated tests from executing.

When ambiguity exists:

* Identify the affected acceptance criterion.
* Document the unanswered question.
* Execute unaffected tests.
* Do not invent expected business behavior.
* Do not classify the ambiguous criterion as verified without sufficient evidence.
* Mark affected coverage incomplete.
* Identify the appropriate decision owner where known.

Only block the affected tests when ambiguity prevents safe or meaningful execution.

Never treat an unanswered question as implied approval.

3.3 Test generation and promotion

Allow generated tests to execute in an isolated or temporary workspace without requiring permanent promotion.

Generated tests must not automatically overwrite existing tests or modify protected regression suites.

Separate:

Execution authorization: Permission to execute an authorized test.

Promotion authorization: Permission to add a generated test to the permanent regression suite.

Promotion remains subject to existing review controls.

Temporary or unpromoted test evidence must be clearly labeled and must not silently satisfy any existing pipeline-reviewed evidence requirement.

3.4 Risk-based execution gates

Allow unattended execution of approved, low-risk testing operations.

Examples:

* Reading Jira stories.
* Inspecting source code.
* Generating test plans.
* Running existing tests.
* Running isolated generated tests.
* Collecting execution evidence.
* Writing verification reports.
* Capturing screenshots.

Require authorization for operations involving:

* Production environments.
* Destructive actions affecting shared data.
* Security-sensitive or unauthorized access.
* Changes to application source code.
* Permanent promotion of generated tests.
* Business risk acceptance.
* Release approval.

The classification and enforcement of these boundaries must be deterministic wherever possible.

Default to least privilege.

Do not rely on an LLM’s self-assessment as the sole enforcement mechanism.

If an operation is blocked, skip that operation, record the reason, and continue unrelated authorized testing.

3.5 Noninteractive execution

Support the same verification workflow in:

* Claude Code interactive mode.
* GitHub Actions pipeline mode.

Pipeline execution must never depend on interactive clarification.

Any question requiring human authority must become a recorded exception.

A missing authorization must not be interpreted as permission.

3.6 Verification outcomes

Preserve the existing meanings of:

VERIFIED: All required in-scope criteria have sufficient qualifying passing evidence under the established verification policy.

INCOMPLETE: Required evidence or coverage is missing, including unresolved requirements or unpromoted evidence that does not qualify for the established pipeline verdict.

NOT VERIFIED: Executed tests produced failures under the established deterministic verification rules.

Distinguish test failures from tests that could not execute.

A skipped or blocked test must never be reported as passed.

Existing machine-readable exit codes and integrations must remain compatible unless an explicit migration is documented and tested.

3.7 Developer-facing findings

Generate findings that developers can act on.

When available, each failure should include:

* Jira story identifier.
* Acceptance criterion.
* Test identifier.
* Expected behavior.
* Observed behavior.
* Failure message.
* Relevant screenshot or trace.
* Relevant API request/response evidence, with secrets redacted.
* Reproduction instructions.
* Environment and source revision.
* Test execution timestamp.

Do not fabricate missing information.

Distinguish confirmed failures from suspected defects and requirement ambiguities.

4. CONSTRAINTS

Follow the existing Intent-Driven Engineering principles.

Particularly:

Principle #19 — Agentic Infrastructure Must Be Governed.

Maintain controlled execution boundaries and auditable behavior.

Principle #20 — Complexity Must Earn Its Existence.

Do not introduce additional architectural complexity without evidence of need.

Principle #21 — Govern the Boundary, Not the Developer.

Govern permissions, side effects, and consequential decisions rather than unnecessarily interrupting testing.

Principle #22 — Architectural Curiosity, Evidentiary Discipline.

Evaluate improvements against actual test evidence.

Principle #23 — Remove the Constraint Before Solving the Problem.

Remove unnecessary approval friction before introducing additional workflow machinery.

Additional constraints:

* Prefer modifying existing skills, scripts, and configuration.
* Reuse existing tests and deterministic validation.
* Preserve auditability.
* Maintain compatibility with existing CI.
* No automatic production access.
* No automatic acceptance of business risk.
* No silent application-code modifications.
* No self-certified AI verification.
* No unnecessary new dependencies.

5. SUCCESS CRITERIA

The implementation is successful when:

SC-01: A tester can invoke Verify SHOP-142 without being required to answer product-owner questions before safe testing begins.

SC-02: Existing API tests execute and produce captured results.

SC-03: Playwright executes end-to-end tests in Chromium and produces evidence.

SC-04: The system generates a test plan from the Jira story and maps executed tests to acceptance criteria.

SC-05: An ambiguous acceptance criterion does not prevent unrelated tests from running.

SC-06: Generated tests can execute without automatic promotion into the permanent regression suite.

SC-07: Unauthorized operations are blocked or skipped while safe operations continue.

SC-08: GitHub Actions runs noninteractively.

SC-09: Reports distinguish passed, failed, skipped, blocked, and unverified evidence without overstating verification.

SC-10: Existing deterministic verdict behavior and machine-readable integrations remain compatible.

SC-11: Existing regression tests continue to pass.

SC-12: No unnecessary infrastructure or architectural components are added.

6. REQUIRED VALIDATION

Before considering implementation complete:

1. Run the existing verification-engine tests.
2. Run the current SHOP-142 demonstration.
3. Verify API execution.
4. Verify Chromium/Playwright execution.
5. Test a story containing an ambiguous acceptance criterion.
6. Confirm unrelated tests continue executing.
7. Test a generated test that has not been promoted.
8. Test a restricted operation and confirm it cannot execute without authorization.
9. Validate pipeline behavior without interactive prompts.
10. Compare verification results against the existing implementation.

Use deliberately failing test cases to confirm that failures are detected and correctly reported.

Preserve evidence from the validation runs.

7. EXPECTED OUTPUTS

Produce:

* Updated verification skill and supporting scripts.
* Updated clarification behavior.
* Updated configuration only where required.
* Regression tests covering the modified behavior.
* Updated README and usage instructions.
* Evidence showing successful execution.
* A concise implementation summary.

The implementation summary must identify:

* What changed.
* What was preserved.
* Which approval gates remain.
* What now runs automatically.
* What remains restricted.
* What tests were executed.
* Which success criteria passed or remain incomplete.

8. STOP CONDITIONS

Stop and request authorization if implementation requires:

* Accessing production systems.
* Modifying business acceptance decisions.
* Removing essential security enforcement.
* Deleting existing user data.
* Introducing a significant architectural dependency.
* Making irreversible or destructive changes.

For ordinary implementation decisions, use existing repository conventions and proceed without unnecessary questions.

If a requirement cannot be safely completed, document the constraint and continue independent work.

9. IMPLEMENTATION INSTRUCTION

First inspect the current implementation and identify the smallest set of changes needed.

Produce a short execution plan.

Then implement, test, and collect evidence.

Do not redesign the application.

Do not introduce additional agents unless an existing capability demonstrably cannot satisfy the intent.

The desired result is a testing tool that automatically performs authorized verification, produces reliable evidence, and escalates only decisions requiring human authority.