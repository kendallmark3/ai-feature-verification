# Architecture
Describe services, APIs, databases, events.

## Feature verification (added)
- `.claude/skills/verify-feature/scripts/verifykit/` is the deterministic engine. Standard library only;
  modules: story, inspect_repo, gaps (Gate 1), plan, guardrails, runner, evidence, report, promote (Gate 2).
- `verify.config.json` is the only place test commands live. The engine never invents a command.
- `demo-app/` is a stand-in product: Node `http` server (no dependencies) serving a React (Vite) build.
- Evidence flows through JUnit XML. See docs/architecture.md.
