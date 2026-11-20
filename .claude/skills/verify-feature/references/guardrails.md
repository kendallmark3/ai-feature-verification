# Guardrails

Enforced by `scripts/verifykit/guardrails.py` and `runner.py`, deterministically, before
anything executes. They don't depend on Claude's judgement, and a missing permission is
never read as permission.

A rule that applies to one suite **blocks that suite only**: it is skipped, the reason is
recorded in `run.json`, the evidence and the report, and the other suites still run. A rule
that applies to the whole run refuses the run (exit 1).

| Rule | Scope | Why |
|---|---|---|
| Commands run without a shell, and the first word must be in `guardrails.allowed_commands`. Pipes, `&&`, `;`, redirects and `$()` are refused. | suite: BLOCKED | A suite can only run the team's test command, nothing chained on. |
| `BASE_URL`, `API_URL` and `TARGET_URL` may not match `deny_url_patterns` (default: `prod`, `production`). | environment: whole run refused · suite `env`: BLOCKED | Verification never runs against production. |
| A suite with `"writes_shared_data": true` runs only in an environment with `"allow_shared_data_writes": true`. | suite: BLOCKED | Tests that create or delete shared data need an explicit, reviewed permission per environment. |
| The command's tool must be installed. | suite: NOT STARTED | Reported as "could not start", never as a failure or a pass. |
| Keys named like `token`, `secret`, `password`, `api_key` must be `${ENV_VAR}` references, not values. | whole run refused | No secrets in the repo or in prompts. |
| Pipeline mode withholds files still marked `@ai-proposed` for the run and restores them afterwards (also after a failure; an interrupted run is recovered on the next run; a restore never overwrites). | file: WITHHELD | Unreviewed tests never count as reviewed evidence. |
| Uncommitted changes to `guardrails.protected_paths` (application code) or to reviewed test files are recorded, and stop a pipeline run from reaching VERIFIED. | evidence | Evidence must come from the committed revision; no silent code or test edits. |
| Each suite is killed after `max_runtime_seconds`. Suites get no stdin. | suite | Runaway or interactive tests don't hang an unattended runner. |
| Failure text and logs are redacted before they are stored: values of secret-named environment variables, `Authorization`/`Cookie` headers, bearer tokens, and secret query or key=value parameters. | evidence | Findings can be shared without leaking credentials. |

Authorising something that is blocked means a person changing `verify.config.json` through
the team's normal review. There is no flag to bypass a guardrail at run time.

Rules for Claude on top of these:

- Use test accounts and data only. Never type real customer data or production credentials.
- Mark suites that create or delete shared data with `writes_shared_data`. Don't add
  `allow_shared_data_writes` to a shared environment yourself.
- Don't install packages, browsers or reporters without asking. If a framework or browser is
  missing, say exactly what's missing and the command the team would use.
- Don't edit `verify.config.json` guardrails or CI workflows without asking.
