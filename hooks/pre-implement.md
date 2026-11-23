Run `hooks/pre-implement.sh` before coding.

It passes when the intent states an Outcome and a Success / Evidence. It does not require requirements, architecture, implementation steps, or exhaustive acceptance criteria.

This repo runs `pre-implement.sh` directly (see `.claude/CLAUDE.md` and CI). The automatic PreToolUse gate comes from installing the intent-drive-starter plugin, which owns `hooks.json` and `pre-implement-hook.sh`.
