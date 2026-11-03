# LoopGuard

A small Python + SQLite prototype for recording agent execution and detecting repeated effort. It accepts Codex JSONL or generic events, emits decisions, and can stop a harness process it launches. No model, server, or credentials are needed for the demo.

## Quick start

```bash
uv sync --locked
# Replay: warnings only; use a new run ID for every invocation.
uv run loopguard --run replay-1 < examples/loop.jsonl
# Live demo: stops after the third identical tool outcome; expected exit code 2.
uv run loopguard --run demo-1 --enforce --command python3 examples/fake_agent.py
# Codex must already be installed and authenticated.
uv run loopguard --run codex-1 --command codex exec --json 'Inspect this repository'
```

Use a unique run ID. Put all LoopGuard options before `--command`.

| Option | Behavior |
| --- | --- |
| Default | Observe and warn; store traces in `trace.sqlite` |
| `--request-stop` | Emit a stop request without enforcing it |
| `--enforce --command …` | Stop the child on a detection |
| `--timeout-secs N` | Independent child runtime limit; default 300 seconds |

stdout emits JSON decisions; stderr includes a final summary and child stderr. Exit codes: **0** success, **1** error, **2** interruption. Cancellation is abrupt: Unix kills the process group; Windows kills only the direct child. File edits are not rolled back.

## Detection and measurements

The rule flags an identical `(tool, arguments, result, failed)` tuple occurring three times in the last sixteen completed tool events. `--repeats` accepts 2–16. Explicit `progress: true` clears the window. Legitimate polling can also trigger this rule.

Generic JSONL accepts these optional fields alongside required `kind`:

```json
{"kind":"tool_end","tool":"shell","arguments":"pytest","result":"missing dependency","failed":true,"progress":false}
{"kind":"usage","input_tokens":1000,"output_tokens":100,"context_tokens":800,"generation_ms":2000,"gap_ms":40000}
```

`generation_tps` is computed only from paired output tokens and nonzero generation milliseconds supplied by the adapter. `gap_ms >= 30000` marks observed silence but never triggers stopping. It is adapter-supplied, not a background stall monitor. Context tokens are optional snapshots, not inferred from input usage. Generic usage events must contain interval deltas, not cumulative totals. Unknown generic fields are rejected to expose schema mistakes.

The Codex adapter recognizes completed command/MCP items and turn usage. Other Codex events are stored raw; unsupported metrics remain unknown. Raw events may contain source code or secrets: the database stays local, and external judge calls occur only when explicitly enabled. Do not publish traces without reviewing their contents.

SQLite stores `runs`, `events`, and `summaries`. Malformed lines are retained with errors. An incomplete run may lack a summary; schema migration is not supported.

## Validation and releases

```bash
uv run python -m unittest discover -s tests
uv run python tests/smoke.py
uv build
```

CI tests Linux, macOS, and Windows. A `v*` tag publishes a universal Python wheel, source archive, and checksums. Python 3.11+ is required.

See the [proposal and experiment plan](PROPOSAL.md). Codex stream reference: [official non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

## Typed Decision API

Opt in with `--decision-url`; set `LOOPGUARD_DECISION_KEY` locally. Use a fresh run ID each time.

| Provider | `--decision-model` | `--decision-auth` | Endpoint |
| --- | --- | --- | --- |
| [TypeSafe Jev](https://docs.typesafe.ai/introduction/quickstart) | `jev-latest` | `bearer` | `https://api.typesafe.ai/v1/systemone` |
| [Cloudflare Clef-Flash](https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-flash/) | `clef-flash` | `bearer` | `https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/cloudflare/clef-flash` |
| [QwenCloud](https://www.qwencloud.com/models/decision-model-preview) | `decision-model-preview` | `raw` | `https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1/systemone` |

For example, with a locally configured Qwen key:

```bash
export LOOPGUARD_DECISION_KEY="$DASHSCOPE_API_KEY"
uv run loopguard --run qwen-1 --decision-auth raw \
  --decision-model decision-model-preview \
  --decision-url https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1/systemone \
  < examples/loop.jsonl
```

A rule trigger sends a single `noul` question; stop probability ≥ 0.9 permits intervention. API failures continue observation. The threshold is provisional.

Calls are limited to eight per run, spaced by four tool events, with a three-second timeout capped by the remaining runtime. Each sends a deterministic summary capped at 6 KB: grouped patterns from the latest 16 tool events since explicit progress, counts, evidence IDs, and short argument/output excerpts. ANSI colors and line endings are normalized; adjacent duplicate lines are collapsed. Full normalized outcomes determine identity, not truncated excerpts. **Excerpts remain unredacted** and omit the task prompt. Missing progress signals mean unknown, not failure. Summaries are lossy; the exact judge input is logged with each decision, while raw events stay in SQLite. The byte budget is not an exact token count. The collector waits for the response while the child continues.

All providers have mock coverage only. Live inference and Qwen's assumed `answers.stop.noul` response remain unverified.
