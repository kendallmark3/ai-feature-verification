# Jira adapters

`verify.config.json → jira.adapter`:

**local** (default) — `jira/<KEY>.json` stands in for the issue. `post` and `approve` append
to its `comments`; `approve --transition Done` sets its `status`. Shape:

```json
{ "key": "SHOP-142", "type": "Story", "status": "In Progress", "summary": "...",
  "description": "...", "acceptance_criteria": ["...", "..."], "comments": [] }
```

`acceptance_criteria` may be a list or a block of text with bullets. Explicit IDs
(`AC-3: ...`) are kept; other items are numbered in order.

**cloud** — Jira REST API v2 over `urllib`:

```json
"jira": { "adapter": "cloud", "base_url": "${JIRA_BASE_URL}", "email": "${JIRA_EMAIL}",
          "api_token": "${JIRA_API_TOKEN}", "ac_field": "customfield_10050" }
```

If `ac_field` is empty, ACs are read from the list under an "Acceptance Criteria" heading in
the description. `approve --transition` uses the workflow transition whose target status
matches the name. Comments are posted as plain text.

An MCP Jira connector can be used for reading context during Gate 1, but posting results
goes through the adapter so the comment format is the same everywhere.
