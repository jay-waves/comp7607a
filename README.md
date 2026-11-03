# LoopGuard

A small Rust + SQLite prototype for recording agent execution and detecting repeated effort. It accepts Codex JSONL or generic events, emits decisions, and can stop a harness process it launches. No model, server, or credentials are needed for the demo.

## Quick start

```bash
cargo build --locked
# Replay: warnings only; use a new run ID for every invocation.
./target/debug/loopguard --run replay-1 < examples/loop.jsonl
# Live demo: stops after the third identical tool outcome; expected exit code 2.
./target/debug/loopguard --run demo-1 --enforce --command python3 examples/fake_agent.py
# Codex must already be installed and authenticated.
./target/debug/loopguard --run codex-1 --command codex exec --json 'Inspect this repository'
```

All LoopGuard options precede `--command`. Default database: `trace.sqlite`. Default child runtime limit: 300 seconds, configurable with `--timeout-secs`. Without `--command`, stdin is recorded until EOF and no process is interrupted. `--request-stop` emits advisory stop requests; `--enforce` actually terminates the owned child and requires `--command`.

stdout contains one JSON decision per input line. stderr contains the final JSON summary and, in command mode, inherited harness stderr. Exit codes: 0 for successful observation, 1 for errors/child failure, 2 for detector or timeout interruption. Records are committed before an intervention. Linux/macOS cancellation uses SIGKILL on the owned process group; it is abrupt, does not roll back file edits, and cannot stop descendants that escape that group. On Windows, cancellation terminates only the direct child; descendants may continue running.

## Detection and measurements

The rule flags an identical `(tool, arguments, result, failed)` tuple occurring three times in the last sixteen completed tool events. `--repeats` accepts 2–16. Explicit `progress: true` clears the window. This detects both immediate repeats and interleaved cycles; it is a suspicion signal, not proof of uselessness. Successful polling can trigger it, so enforcement is opt-in.

Generic JSONL accepts these optional fields alongside required `kind`:

```json
{"kind":"tool_end","tool":"shell","arguments":"pytest","result":"missing dependency","failed":true,"progress":false}
{"kind":"usage","input_tokens":1000,"output_tokens":100,"context_tokens":800,"generation_ms":2000,"gap_ms":40000}
```

`generation_tps` is computed only from paired output tokens and nonzero generation milliseconds supplied by the adapter. `gap_ms >= 30000` marks observed silence but never triggers stopping. It is adapter-supplied, not a background stall monitor. Context tokens are optional snapshots, not inferred from input usage. Generic usage events must contain interval deltas, not cumulative totals. Unknown generic fields are rejected to expose schema mistakes.

The Codex adapter recognizes completed command/MCP items and turn usage. Other Codex events are stored raw; unsupported metrics remain unknown. Raw events may contain source code or secrets: the database stays local, and external judge calls occur only when explicitly enabled. Do not publish traces without reviewing their contents.

## Storage and extension points

SQLite tables: `runs` (run identity), `events` (sequence, receipt timestamp, raw/normalized payload, decision), and `summaries` (final outcome). Reusing a run ID fails. Malformed lines are preserved with a parse error and do not trigger intervention. Fatal collector errors terminate an owned child; an incomplete run may have no summary. Database creation is idempotent, but schema migration is not yet supported.

The generic event schema is the integration boundary for another harness. Redaction, token streaming, automatic redirection, and an MCP server are deliberately deferred; there is no claim that a skill or MCP alone can intercept host execution.

## Validation and releases

```bash
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
cargo build --locked
python3 tests/smoke.py
```

CI runs these checks on Linux, macOS, and Windows. Pushing a `v*` tag builds Linux x86_64, macOS ARM64, and Windows x86_64 archives, including bundled SQLite, and publishes them with SHA-256 checksums to GitHub Releases. Linux builds use the runner's glibc and are not guaranteed compatible with older distributions. Publication is configured but has not been executed locally.

See [proposal](proposal.md) and [experiment plan](docs/experiments.md). Codex stream reference: [official non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

## Typed Decision API

Opt in with `--decision-url`. Configure `LOOPGUARD_DECISION_KEY` in your shell (never commit it). Examples:

```bash
# TypeSafe Jev: key from the TypeSafe console
export LOOPGUARD_DECISION_KEY="$TYPESAFE_API_KEY"
./target/debug/loopguard --run jev-1 --decision-url https://api.typesafe.ai/v1/systemone --decision-model jev-latest < examples/loop.jsonl

# Cloudflare: account ID plus a Workers AI API token
export LOOPGUARD_DECISION_KEY="$CLOUDFLARE_AUTH_TOKEN"
./target/debug/loopguard --run clef-1 --decision-url "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/cloudflare/clef-flash" --decision-model clef-flash < examples/loop.jsonl
```

The adapters use `state + questions` with a single `noul` question. Direct TypeSafe responses and Cloudflare's `result` envelope are supported. The rule triggers a decision call; probability >= 0.9 permits a warning/stop request. Actual stopping still requires `--enforce --command ...`. This is a provisional threshold, not a calibrated guarantee.

At most eight calls per run, spaced by at least four completed tool events; no retries. Each call sends the latest eight normalized events, truncated to 2,000 characters each. This includes tool arguments/results, is **not redacted**, and omits the original task prompt. Only opt in for traces suitable for the chosen provider. Missing context can reduce judgment quality. Usage, probability, latency, and returned model are stored in the decision; failures continue observation. A request takes at most three seconds, capped by remaining child runtime. The synchronous collector pauses ingestion during the call while the child continues; this is a prototype limitation.

References: [TypeSafe](https://docs.typesafe.ai/introduction/quickstart), [Cloudflare](https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-flash/).

### QwenCloud decision-model-preview

The [model page](https://www.qwencloud.com/models/decision-model-preview) documents the same System One request shape, with a raw Authorization header:

```bash
export LOOPGUARD_DECISION_KEY="$DASHSCOPE_API_KEY"
./target/debug/loopguard --run qwen-1 \
  --decision-url https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1/systemone \
  --decision-model decision-model-preview --decision-auth raw \
  < examples/loop.jsonl
```

`--decision-auth raw` sends the key exactly as configured; the default `bearer` adds the Bearer prefix for Jev/Clef. The Qwen page documents the request but does not show a response example. The adapter currently expects the existing typed `answers.stop.noul` response and fails open on any different shape. All providers have local mock coverage only; authenticated inference and Qwen’s response schema remain unverified.
