# Repository Rules
Read intent/current-feature.md first, including any deltas appended to it.
Run hooks/pre-implement.sh before implementing.
Build the smallest useful delta, then let the human observe it and decide: continue or stop.
Always write tests.
Respect architecture (docs/architecture.md).

## Feature verification
- To verify a story, use the `verify-feature` skill. Gate 1 is `clarify-story`, Gate 2 is `promote-tests`.
- The engine is `.claude/skills/verify-feature/scripts/verify.py` (stdlib Python). Run it from the repo root.
- The demo app is `demo-app/` (React + Node, Playwright + node:test). Story: `jira/SHOP-142.json`.
- Never answer Gate 1 questions, promote tests or approve a story on your own. People do that.
- Don't change product code in `demo-app/server` or `demo-app/web` while verifying; report defects instead.
