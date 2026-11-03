# Agent guidance

- Keep LoopGuard small, local-first, and compatible with Codex JSONL and the generic event schema.
- Preserve observation-only defaults; treat missing metrics and judge failures as unknown, not evidence to stop.
- External decision calls send trace contents. Never commit credentials or claim unredacted traces are safe to share.
- Update README and proposal when behavior or experiment scope changes.
- Use uv for dependencies, execution, and packaging.
- Validate with `uv run python -m unittest discover -s tests`, `uv run python tests/smoke.py`, and `uv build`.
