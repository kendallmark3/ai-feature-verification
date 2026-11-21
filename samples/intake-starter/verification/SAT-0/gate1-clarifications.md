# Gate 1 · Clarifications for SAT-0

**Story:** Client submits a project intake

Testing does not wait for these answers. Each open question marks only the criterion it
names as UNRESOLVED: its tests may still run, but it can never be reported as passing until
the owner answers. An answer can be a decision, a rule, an example, or `Accepted risk: <why>`.
Questions from the deterministic rules come first; Claude adds judgement questions below
them with IDs `Q-AI-n`.

Check with: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/verify-feature/scripts/verify.py" gate1 SAT-0 --check`

<!-- Claude: add judgement questions below this line as ## Q-AI-n · AC-x · TOPIC -->
