# Intake starter · Saturday dress rehearsal (SAT-0)

A Spring Boot API (`backend/`, Maven, JUnit 5) and a React page (`frontend/`, Vite), the shape
of an Intent-Driven Saturday build. It started as Spring Initializr and Vite leave a project:
JUnit in the backend, no tests in the front end. `verification/SAT-0/` is the rehearsal record
(INTENT-003): framework proposal and approval, plan, evidence, report.

Result: every criterion of `jira/SAT-0.json` is PASS from a test that ran (AC-1 to AC-3 Java,
AC-4 and AC-5 Playwright with screenshots). The verdict is INCOMPLETE only because the tests are
still `@ai-proposed` (Gate 2) and the run was interactive.

## Run it

Needs JDK 21+, Maven 3.9+, Node 20+. From this folder (`V` is the engine in this repo):

```bash
V=../../.claude/skills/verify-feature/scripts/verify.py
(cd frontend && npm install && npx playwright install chromium)
python3 $V all SAT-0 --mode interactive
```

Playwright starts the API (`mvn spring-boot:run`, port 8080) and the UI (Vite, port 5310). The
runner sets `CI=1`, so a server already on either port is **not** reused and the suite stops
with "already used": stop your own dev servers first, or point `BASE_URL` at a running host.

## Saturday, step by step

1. **Before the day:** authorise the Atlassian connector in Claude; export `JIRA_BASE_URL`,
   `JIRA_EMAIL`, `JIRA_API_TOKEN` in the shell that starts Claude Code.
2. **Story into Jira:** ask Claude to create the epic and stories through the connector using
   `references/story-template.md` (criteria under "Acceptance Criteria", exact messages and
   numbers, API vs page stated).
3. **Repo:** `backend/` from Spring Initializr (Maven, Java 21, Web), `frontend/` from Vite React.
4. **`verify.py init`** at the repo root: one suite for `backend/`; notes for the `pom.xml`
   reporter and the untested front end.
5. **`verify.py frameworks SAT-1 --propose`**, a named person reads `FRAMEWORK_PROPOSAL.md` and
   runs `--approve --by "Name"`, then `--apply` and the printed `npm install` line.
6. **"verify SAT-1"** in Claude: story, Gate 1, plan, tests in both halves, run, report.
7. Gate 2 (promote) and Gate 3 (approve) stay with people.
