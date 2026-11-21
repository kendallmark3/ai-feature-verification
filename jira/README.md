# Simulated Jira

No Jira instance needed. Each `<KEY>.json` here stands in for a Jira issue, and the
`local` adapter in `verify.config.json` reads it and appends comments to it, exactly
where the cloud adapter would call the Jira REST API.

`SHOP-142.json` is deliberately an ordinary story — vague words, no thresholds, no
examples, no mention of expiry or case rules. That is the point: Gate 1 should catch it.

To use a real Jira instead, set in `verify.config.json`:

```json
"jira": {
  "adapter": "cloud",
  "base_url": "${JIRA_BASE_URL}",
  "email": "${JIRA_EMAIL}",
  "api_token": "${JIRA_API_TOKEN}",
  "ac_field": "customfield_10050"
}
```

and export those three variables (or export them first and run `verify.py init`, which writes
this block for you). See `install-plugin.md` for the API token. `IDS-3.json` here is a snapshot
of a real Jira Cloud story, kept for the EXPERIMENT-001 tests in `tests/ids3/`. If `ac_field` is left out, the acceptance criteria are
read from the list under an "Acceptance Criteria" heading in the description.
