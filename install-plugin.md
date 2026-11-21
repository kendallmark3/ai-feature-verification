# Install the AI Feature Verification plugin

Verify a Jira story in your own repository: Claude pulls the story, plans against its
acceptance criteria, writes tests in the framework you already use, runs them, and reports
evidence per criterion. You decide at three gates (clarify, promote, approve).

## Before you start

- [Claude Code](https://claude.com/claude-code) (the `claude` command)
- `git` and Python 3.10+ (the engine is standard-library Python; nothing to pip install)
- A repository with tests that write JUnit XML (pytest, Jest, Vitest, Playwright, Cypress,
  node:test, Maven, Gradle, Go, .NET)
- For real Jira: access to a Jira Cloud site and your own Atlassian API token

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
| Jira can't be reached, or `init` writes the `local` adapter | The `JIRA_*` variables aren't in Claude Code's environment: export them in your shell profile, open a new terminal, start `claude` from it |
| Playwright: `Executable doesn't exist ... chrome-headless-shell` | Install the browser in your repo (`npx playwright install chromium`), or set `channel: 'chrome'` in your Playwright config to use your installed Chrome |
| A suite runs but shows no results | Its `junit` path in `verify.config.json` doesn't match where the framework writes JUnit XML |

## Update or remove

```bash
claude plugin marketplace update ai-feature-verification          # fetch the latest version
claude plugin update ai-feature-verification@ai-feature-verification
claude plugin uninstall ai-feature-verification@ai-feature-verification
```
