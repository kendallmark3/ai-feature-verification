# Install the AI Feature Verification plugin

Verify a Jira story in your own repository: Claude pulls the story, plans against its
acceptance criteria, writes tests in the framework you already use, runs them, and reports
evidence per criterion. You decide at three gates (clarify, promote, approve).

## Before you start

- [Claude Code](https://claude.com/claude-code) (the `claude` command)
- `git` and Python 3.10+ (the engine is standard-library Python; nothing to pip install)
- A repository with tests that write JUnit XML (pytest, Jest, Vitest, Playwright, Cypress,
  node:test, Maven, Gradle, Go, .NET). A web front end or Python project with no tests yet is
  fine too: see [What it needs on your machine](#what-it-needs-on-your-machine).
- For real Jira: access to a Jira Cloud site and your own Atlassian API token

## What it needs on your machine

The plugin installs nothing and brings no test framework. It runs the commands your project
already uses (`mvn test`, `npx playwright test`, `pytest`, ...) and reads their JUnit XML.

| What | Who provides it | Notes |
|---|---|---|
| The plugin: 3 skills + the `verify.py` engine | `claude plugin install` | Standard-library Python only. No pip, no npm. |
| Python 3.10+ | Your machine | Already on macOS and most Linux. |
| Your project's toolchain (JDK + Maven, Node + npm, Python + pytest, ...) | Your project | Whatever you already need to build and test it. Same on CI. |
| Playwright browsers | Once per machine, in your repo | `npx playwright install chromium` (CI: `npx playwright install --with-deps chromium`), or set `channel: 'chrome'` to use your installed Chrome. |

**Caveats:**

- **One-time setup when a project has no tests.** For a front end with no test framework
  (a fresh Vite/React app, for example), Claude proposes Playwright. For Python with no tests,
  it proposes pytest. Nothing is written until a named person approves:
  `verify.py frameworks <KEY> --propose`, then `--approve --by "Name"`, then `--apply`. Then
  you run the install line it prints (for example `cd frontend && npm install && npx playwright
  install chromium`). A project that already has a framework never gets a second one.
- **Spring Boot / Maven with JUnit 5.** Surefire writes the method name, not the
  `@DisplayName`, to its XML, so `KEY AC-n` tags are lost. You need a one-time block in
  `pom.xml`. `init` shows it, and `frameworks --propose` adds it after approval. This edits
  the build file; it doesn't install anything.
- **Free ports.** Playwright starts your app itself and won't reuse a server already running
  on its ports (the runner sets `CI=1`). The defaults are 8080 for a Spring Boot API and 5310
  for the UI. Stop your own dev servers first, or set `BASE_URL` to a running DEV/UAT host.
- **pytest on Homebrew Python (macOS).** `pip install pytest` is refused (PEP 668). Use a
  virtualenv (`python3 -m venv .venv && . .venv/bin/activate && pip install pytest`), or
  `python3 -m pip install --user --break-system-packages pytest`. Only needed if your project
  uses pytest.
- **Nothing from the plugin's own repo comes along.** `demo-app/`, `samples/` and `tests/` live
  in the source repo, not in the plugin, so they add no dependencies to your machine.

## Install

```bash
claude plugin marketplace add kendallmark3/ai-feature-verification
claude plugin install ai-feature-verification@ai-feature-verification
```

Start a new Claude Code session, then check that `claude plugin list` shows
`ai-feature-verification@ai-feature-verification` as `✔ enabled`, and that
`claude plugin details ai-feature-verification@ai-feature-verification` lists 3 skills:
`clarify-story`, `promote-tests`, `verify-feature`.

Already inside a Claude Code session? The same two steps as slash commands:

```text
/plugin marketplace add kendallmark3/ai-feature-verification
/plugin install ai-feature-verification@ai-feature-verification
```

It installs at user scope, so it works in every repo you open on that machine.

## Connect your Jira (once per machine)

1. Create an API token: **id.atlassian.com → Security → Create and manage API tokens**.
2. Export these in your shell profile (`~/.zshrc`, `~/.bashrc`), not in any project file:

   ```bash
   export JIRA_BASE_URL="https://your-site.atlassian.net"
   export JIRA_EMAIL="you@example.com"
   export JIRA_API_TOKEN="…"          # your token; never commit it, never paste it into a chat
   ```

3. Open a new terminal and start Claude Code from it, so it sees the variables.

Rather keep them per project? Put the same three lines (without `export`) in a `.env` file at
your repo root, **add `.env` to `.gitignore` first**, and load it before starting Claude Code:
`set -a; . ./.env; set +a; claude`.

**Get these right, or every call fails:**

- `JIRA_EMAIL` must be the email of the Atlassian account that **created the token**. A token
  only works with its own account's email, not with another address you also use.
- Use **Create API token**, not "Create API token with scopes". Scoped tokens don't work
  against your site URL.
- That account must be able to open the story in the browser.

**Check the connection** before verifying anything (prints your name, never the token):

```bash
python3 -c "import os,base64,json,urllib.request as u;r=u.Request(os.environ['JIRA_BASE_URL'].rstrip('/')+'/rest/api/2/myself',headers={'Authorization':'Basic '+base64.b64encode((os.environ['JIRA_EMAIL']+':'+os.environ['JIRA_API_TOKEN']).encode()).decode()});print('OK, logged in as',json.load(u.urlopen(r))['displayName'])"
```

`OK, logged in as …` means you're set. `HTTP Error 401` means the email and token don't
belong together, or the token was revoked or has expired. Note that Jira answers a request
that isn't logged in with **404** "issue does not exist or you do not have permission" for
any issue, so a 404 on a story you can see in the browser almost always means the login, not
the story, is the problem.

The engine reads them from the environment at run time. `verify.config.json` only ever holds
`${JIRA_API_TOKEN}`-style references, and the engine refuses to run if a literal secret is
written there.

Using the shared **Intent Driven Saturdays** board? Ask Mark for access to the Jira site, then
set `JIRA_BASE_URL=https://intentdrivenengineering.atlassian.net` with your own email and token.

## Verify a story

In your repository:

> Verify IDS-5.

or `/ai-feature-verification:verify-feature IDS-5`.

The first time, Claude runs `init`, which finds your test frameworks and writes
`verify.config.json` (with the real-Jira block when `JIRA_BASE_URL` is set). It shows you
the suggested test commands and waits for you to confirm them. Check that every suite you
actually run is listed and add any it missed: detection is a starting point, and a test
command hidden behind an npm script (for example `node --test` in `npm run test:api`) may not
be found. After that it runs the whole loop on its own and reports back.

No Jira yet? Put a story at `jira/<KEY>.json` in your repo and keep the `local` adapter;
`jira/SHOP-142.json` in this repo shows the format.

### Write stories it can test

Put the acceptance criteria in the story's **Description**, as a numbered or bulleted list
under an **Acceptance Criteria** heading. Keep the Summary short: Jira cuts it at 255
characters. A story with no criteria stops at Gate 1, and nothing runs.

## What it brings back

- `verification/<KEY>/VERIFICATION_REPORT.md`: verdict, a row per criterion, and what passed,
  failed, was skipped or was blocked
- `verification/<KEY>/gate1-clarifications.md`: questions for the story owner (testing doesn't wait for them)
- New tests marked `@ai-proposed` until a person promotes them (Gate 2)
- With your OK, a summary comment on the Jira story

## Skills

| Skill | Slash command | When |
|---|---|---|
| `verify-feature` | `/ai-feature-verification:verify-feature <KEY>` | "verify IDS-5", "is this story done?", "test this ticket" |
| `clarify-story` | `/ai-feature-verification:clarify-story <KEY>` | "is this story ready / testable?" (Gate 1) |
| `promote-tests` | `/ai-feature-verification:promote-tests <KEY>` | "review the generated tests" (Gate 2) |

## If something doesn't work

| Symptom | Fix |
|---|---|
| The skills don't show up | Start a new Claude Code session after installing; check `claude plugin list` |
| Jira says 401, or 404 on a story you can open in the browser | The email isn't the token's account, or the token is scoped, revoked or expired. Run the connection check under [Connect your Jira](#connect-your-jira-once-per-machine) |
| Jira can't be reached, or `init` writes the `local` adapter | The `JIRA_*` variables aren't in Claude Code's environment: export them in your shell profile, open a new terminal, start `claude` from it |
| Playwright: `Executable doesn't exist ... chrome-headless-shell` | Install the browser in your repo (`npx playwright install chromium`), or set `channel: 'chrome'` in your Playwright config to use your installed Chrome |
| A suite runs but shows no results | Its `junit` path in `verify.config.json` doesn't match where the framework writes JUnit XML |
| Playwright: `http://127.0.0.1:5310 is already used` or `EADDRINUSE` | Another server holds that port. Stop it (`lsof -nP -iTCP:<port> -sTCP:LISTEN` shows which), or set `BASE_URL` |
| Java tests pass but every criterion shows no evidence | The Surefire reporter block is missing from `pom.xml`, so tags were lost. Run `init` or `frameworks <KEY> --propose` |
| `No module named pytest` | Your `python3` changed (for example a Homebrew upgrade) and has no pytest. See the pytest caveat under [What it needs on your machine](#what-it-needs-on-your-machine) |

## Update or remove

```bash
claude plugin marketplace update ai-feature-verification          # fetch the latest version
claude plugin update ai-feature-verification@ai-feature-verification
claude plugin uninstall ai-feature-verification@ai-feature-verification
```
