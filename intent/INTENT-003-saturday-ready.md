# INTENT-003 · Saturday-ready verification

## Outcome
On the next Intent-Driven Saturday, Claude puts a story (or an epic with stories) into Jira,
the team builds a **Spring Boot API with a React front end** in 3–4 hours, and "verify SAT-1"
comes back with a real verdict across both halves: each testable criterion PASS or FAIL from
tests that ran, Java and browser alike.

The Saturday app itself is still open. The likely one is an **intent intake site**: a client
describes what they want (an e-commerce storefront, a website, an API), attaches artifacts and
reasoning, and the site turns that into an intent package we can build from. This intent
doesn't build that app; it makes the harness ready for it.

## Observation
- **Java tagging is broken by default (measured 2026-11-21, JDK 21, Maven 3.9.14,
  Surefire 3.5.2, JUnit 5.11.4):** a test with
  `@DisplayName("SAT-1 AC-1 …")` is written to Surefire's XML as `name="submits"` (the method
  name), so the tag is lost and the test counts as untagged. With Surefire's
  `JUnit5Xml30StatelessReporter` and `usePhrasedTestCaseMethodName=true`, the XML carries the
  display name and the engine's `parse_junit` reads it as a tagged pass. Our guide
  (`ac-tagging.md`) tells people to use `@DisplayName` without mentioning this.
- **Gradle is unmeasured.** Saturday uses Maven (decided), so Gradle is a later check.
- **JavaScript and Python are proven** where tests exist: SHOP-142 (node:test + Playwright,
  desktop and Pixel 7) and IDS-3 (pytest, live Jira, 25 passed).
- **Saturday repos are two apps in one repo** (`backend/` Spring Boot, `frontend/` React).
  Detection of build files in subfolders is untested.
- **Prototypes often have no tests.** Spring Initializr ships JUnit 5 and
  `spring-boot-starter-test`, so the backend has a framework. A fresh Vite React app has none,
  and the old rule "never add a test framework" left nothing to run there.
- **The engine can't create Jira issues.** It reads issues and posts comments only
  (INTENT-002). Creating the Saturday story is a new Jira write.

## Decisions (Mark Kendall, 2026-11-21)
Use the team's framework when there is one. When a project has none, propose the default and
add it only after a named person approves: **Playwright** for web front ends, **pytest** for
Python.

- The Saturday backend uses **Maven**.
- Claude creates Jira issues through the **Atlassian connector**, not the engine.

## Outputs
1. **Java tagging that works.**
   - `init` on a Maven project checks for the phrased-name reporter. When it is missing, `init`
     shows the exact `pom.xml` block and doesn't edit the build file unless the person approves.
   - `ac-tagging.md` and `framework-adapters.md` corrected.
   - Gradle: deferred (Saturday uses Maven).
2. **One repo, two apps.** `init` finds `backend/pom.xml` and `frontend/package.json` and
   proposes one suite for each, with the right `cwd` and JUnit path.
3. **React defaults.** For a front end with no tests: Playwright, with a JUnit reporter and a
   `webServer` that starts both the API and the UI. Vitest documented for unit tests.
4. **Approval before anything is added.** The proposal lists the files and dev dependencies.
   Nothing is written or installed until a named person approves, and the approval is recorded
   with name and date in `verification/<KEY>/`.
5. **Getting the story into Jira (decided: Atlassian connector).** Claude creates the Saturday
   epic and stories through the Atlassian connector, authorised in Claude before the day; the
   engine is unchanged. Document it with a story template whose criteria the harness can test
   (an "Acceptance Criteria" list in the description, observable results, real numbers).
6. **Dress rehearsal.** `samples/intake-starter/`: a minimal Spring Boot API plus a React page,
   a simulated story `SAT-0`, verified end to end before Saturday.
7. **Small doc gaps:** `jest-junit` for Jest, a Mocha line, and plain `unittest` projects run
   through pytest.

## Success / Evidence
- In the dress rehearsal, every testable criterion of SAT-0 is PASS or FAIL from tests that
  ran, with Java tests counted as tagged. No report reason says a suite, framework or tag is
  missing.
- `init` on the dress-rehearsal repo proposes both suites; on this repo's demo app it never
  proposes a second framework.
- Without approval, `init` doesn't change `pom.xml` and adds no framework; tests show both.
- SHOP-142 and IDS-3 verdicts are unchanged. `python3 -m unittest discover -s tests/verifykit`
  passes, with new tests for nested detection, the Maven reporter check and the approval check.

## Constraints / Boundaries
- Engine stays Python standard library only. Frameworks and build config are changed in the
  project being verified, never in the engine, and only with approval.
- Only the defaults named above. Never add a framework next to an existing one or replace one.
- No change to guardrail allow-lists (`mvn`, `npx`, `node`, `python3` are already allowed) or
  CI workflows. No change to demo-app product code.
- No new Jira writes in the engine: issues are created through the Atlassian connector.
- Credentials only from the environment. Gates 1–3 stay human decisions.
- Out of scope: building the Saturday app, AWS hosting, .NET and Angular.

## Stop
After the dress rehearsal reaches a real verdict, stop and show the report before Saturday.
