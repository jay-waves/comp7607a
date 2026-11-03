# Agent guidance

- Keep LoopGuard small, local-first, and compatible with Codex JSONL and the generic event schema.
- Preserve observation-only defaults; treat missing metrics and judge failures as unknown, not evidence to stop.
- External decision calls send trace contents. Never commit credentials or claim unredacted traces are safe to share.
- Update README and proposal when behavior or experiment scope changes.
- Use uv for dependencies, execution, and packaging.
- Validate with `uv run python -m unittest discover -s tests`, `uv run python tests/smoke.py`, and `uv build`.

## Development scope and file organization

- Prefer the smallest complete change. Reuse existing code and conventions before introducing abstractions, dependencies, configuration, or directories.
- Keep one authoritative implementation and data source for each behavior. Do not leave duplicate helpers, alternative implementations, unused scaffolding, or speculative extension points.
- Add a file only when it has a clear responsibility that does not fit an existing file. Keep related code together; do not split tiny functions into separate modules without a concrete benefit.
- Keep temporary scripts, debug output, caches, build artifacts, trace databases, and local experiment outputs out of version control. Use /tmp for disposable investigation files.
- Keep Python tooling at the root and frontend tooling inside presentation/. Do not introduce a root Node workspace or duplicate lockfiles. presentation/ uses npm and package-lock.json as its frontend exception to the uv rule.
- Add dependencies only for a demonstrated need; prefer existing capabilities. Commit manifest and lockfile updates together and avoid unrelated dependency upgrades.
- Write tests for meaningful behavior and failure cases. Avoid tests that merely mirror implementation and avoid broad refactors unrelated to the requested change.

## CI/CD

- Keep workflows in .github/workflows and reuse existing jobs where practical. CI must use locked dependencies and the same validation commands documented for local development.
- Required checks must fail on errors; do not hide failures with continue-on-error, ignored exit codes, or skipped tests to obtain a green build.
- Pull requests validate changes without production deployment. Pages deployment runs only from main after a successful presentation build, including manually triggered deployments.
- Grant the minimum job permissions. Keep Pages write and OIDC permissions in the deployment job; never expose deployment credentials to pull-request code or use pull_request_target to execute untrusted changes.
- Publish only intended artifacts: presentation/dist for Pages, Python release artifacts through the existing release workflow. Never upload the entire working tree, traces, databases, or environment files.
- Keep deployment concurrency explicit to avoid overlapping releases. Do not add a second workflow targeting the same Pages site without replacing or coordinating the existing one.
- Document changes to triggers, deployment prerequisites, and output locations. Distinguish local validation from a successful remote workflow run or live deployment.

## Git and submission management

- Inspect git status and diff before editing and before submission. Preserve unrelated user changes; do not reset, stash, clean, or overwrite them to simplify the task.
- Keep commits focused on a single reviewable purpose. Stage explicit paths or hunks; review staged diff and whitespace errors before committing. Do not use git add . indiscriminately.
- Use concise imperative commit subjects, optionally prefixed with feat:, fix:, docs:, or ci:. Explain non-obvious rationale in the body; do not claim checks that were not run.
- Commit source, documentation, and relevant lockfiles together. Do not commit node_modules, dist, generated presentations, credentials, or raw traces.
- Before committing implementation changes, run the applicable validation above and report failures or unavailable checks. Documentation-only guidance edits need a diff/whitespace review, not a full rebuild.
- Do not amend published history, force-push, create tags, merge, or publish releases unless explicitly authorized. Commit and push when requested; otherwise leave a clear, reviewable working-tree diff.
- Final reports state what changed, which checks passed, and any remaining deployment/setup step. Never describe authored workflow configuration as an already deployed site.
