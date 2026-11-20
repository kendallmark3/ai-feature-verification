# Guardrails

Enforced by `scripts/verifykit/guardrails.py` before anything runs:

| Rule | Why |
|---|---|
| Commands run without a shell, and the first word must be in `guardrails.allowed_commands`. Pipes, `&&`, redirects and `$()` are refused. | A suite can only run the team's test command, nothing chained on. |
| `BASE_URL`, `API_URL` and `TARGET_URL` may not match `deny_url_patterns` (default: `prod`, `production`). | Verification never runs against production. |
| Keys named like `token`, `secret`, `password`, `api_key` must be `${ENV_VAR}` references, not values. | No secrets in the repo or in prompts. |
| Pipeline mode refuses files still marked `@ai-proposed`. | Gate 2: nothing unreviewed reaches CI. |
| Each suite is killed after `max_runtime_seconds`. | Runaway tests don't hang a runner. |

Rules for Claude on top of these:

- Use test accounts and data only. Never type real customer data or production credentials.
- In shared environments (DEV/UAT), prefer read-only checks; ask before tests that create or
  delete shared data.
- Don't install packages, browsers or reporters without asking. If a framework or browser is
  missing, say exactly what's missing and the command the team would use.
- Don't edit `verify.config.json` guardrails or CI workflows without asking.
