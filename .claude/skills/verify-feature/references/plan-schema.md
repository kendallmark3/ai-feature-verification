# plan.json

`verify.py plan <KEY> --init` creates it from the story. Claude fills it in; people
review it; `--check` validates it; `--render` writes `VERIFICATION_PLAN.md`.

```json
{
  "story": "SHOP-142",
  "summary": "Discount codes at checkout",
  "tagging": "Every test that verifies a criterion names it in its title, e.g. 'SHOP-142 AC-1 ...'",
  "acs": [
    {
      "id": "AC-2",
      "text": "Valid codes apply the discount to the total",
      "clarified_as": "SAVE10 takes 10% off; FLAT20 takes $20 off orders of $50+. Codes are case-insensitive. (Q-1, Q-AI-2)",
      "disposition": "verify",
      "reason": "",
      "checks": [
        {
          "id": "AC-2.a",
          "description": "API returns discount and new total for SAVE10 and FLAT20",
          "suite": "api",
          "expected_evidence": ["junit: api", "response body values"]
        }
      ]
    },
    {
      "id": "AC-4",
      "text": "Should be fast",
      "clarified_as": "",
      "disposition": "not-verifiable",
      "reason": "PO deferred the threshold (Q-3). No number, so no pass/fail.",
      "checks": []
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `clarified_as` | The testable rule, from Gate 1 answers. Cite the question IDs. Empty only if the AC was already precise. |
| `disposition` | `verify`, `not-verifiable` (can't be tested as written, even after Gate 1) or `out-of-scope` (agreed not to verify here). |
| `reason` | Required unless `verify`. Written so a reviewer can accept or reject it. |
| `checks[].suite` | A suite name from `verify.config.json`. Coverage needs at least one tagged test per planned suite. |
| `checks[].expected_evidence` | What will prove it: junit result, screenshot, response values, metric, log line. |

Coverage is counted per AC and suite, from test titles (see `ac-tagging.md`). Check IDs
(`AC-2.a`) are for people reading the plan; tests only need the AC ID.
