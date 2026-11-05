# LoopGuard

LoopGuard investigates when and how to intervene in stalled agent execution so that the remaining budget produces useful progress.

The current prototype is a local Python + SQLite monitor for recording agent execution and detecting repeated tool outcomes. It accepts Codex JSONL or generic events, emits decisions, and can stop a harness process it launches. No model, server, or credentials are needed for the demo.

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

CI tests Linux, macOS, and Windows. A `v*` tag publishes a universal Python wheel, source archive, standalone `loopguard-presentation.html`, and checksums. Python 3.11+ is required.

See the [proposal and experiment plan](PROPOSAL.md) and [related work and comparison design](RELATED_WORK.md). Codex stream reference: [official non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

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

## Presentation

The [presentation](presentation/README.md) presents the research problem, monitoring method, evaluation protocol, illustrative comparisons, and limitations. It uses reveal.js, React, TypeScript, Markdown, visx, and Paul Tol Muted CSS tokens. All plotted values are synthetic; no experimental findings are claimed.

The Pages workflow validates pull requests and deploys `presentation/dist` from `main`. Configure the repository's Pages source as GitHub Actions. Python uses uv; frontend tooling remains isolated in `presentation/`.

Candidate extension environments are DeepSeek Harness, Grok Build, and Cursor Agent CLI. Codex remains the implemented adapter and primary evaluation scope; candidate integrations and cross-harness experiments are not yet implemented.

The presentation uses Pele to render Mermaid architecture, decision-flow, evidence-pipeline, sequence, and evaluation diagrams with the same Georgia and Paul Tol Muted styling. These diagrams describe implemented monitoring semantics or explicitly planned evaluation.

For offline distribution, `npm run build:single --prefix presentation` produces `presentation/dist-single/index.html` with scripts and styles inlined.

## Experiment plan

Compare **when to intervene** and **how to intervene** in two stages, under the same total task budget:

| Stage | Hold fixed | Compare |
| --- | --- | --- |
| How | Base model, initial reasoning effort, trigger | Continue unchanged; increase thinking; reduce/disable thinking; restart context |
| When | Intervention selected on development tasks | No intervention; signal rules; the same rules plus optional Jev confirmation |

Candidate signals are repeated unchanged outcomes, sustained generation-TPS decline, and abrupt context growth. These indicate suspected degradation, not proven failure. Missing metrics remain unknown; current Codex events do not provide reliable generation TPS or context snapshots. Thinking controls must be supported by the model interface, not simulated with tags.

A context restart retains the goal, code state, failure summary, and next hypothesis while keeping reasoning effort unchanged. All attempts and judge calls share one budget. Measure task success and total cost, plus recovery after intervention; false interventions are a quality diagnostic. See the [protocol and decision tree](PROPOSAL.md#experiments).

**Planned capabilities:** metric-based triggers, reasoning-effort changes, and context restarts. The current implementation observes, warns, or stops an owned process, optionally after judge confirmation. No live agent results are claimed.

**Planned task extensions:** SQL performance optimization (JOB / Effi-SQL) and MaxSAT optimization, measuring validated runtime improvements and feasible objective improvements respectively. The [experiment plan](PROPOSAL.md#experiments) outlines candidate sources and contamination controls: separate public baselines from freshly generated local instances, split by template/generator family, and validate references. These task environments and detailed protocols are not implemented; fresh instances reduce exposure risk without proving contamination-free evaluation.

Task environments must remain lightweight and local: prefer embedded SQLite for suitable SQL tasks and small MaxSAT instances with a local checker. PostgreSQL is optional when benchmark compatibility requires it. Bound resource use and setup/reset costs; label engine ports or reduced workloads as adaptations rather than original benchmark results. See the environment requirements in the experiment plan.

## Small sandbox pilot

[Sandbox instructions and task definitions](experiments/README.md) provide six
paired fixtures: recoverable/persistent service failure, consistent/conflicting
requirements, and a broken/already-complete function. Build the lightweight image:

```bash
docker build -t loopguard-sandbox:v1 -f experiments/Dockerfile experiments
docker run --rm -it --network none --cpus 1 --memory 512m --pids-limit 128 -e TASK=retry-control loopguard-sandbox:v1
```

Every new container starts clean. The image includes Python, uv, bash, git, curl,
ripgrep, jq, patch, procps, findutils, and less; model clients are not installed.
Fixtures are implemented, not experimental results. Contradictory requirements
need human review; the local mock service is inspectable and call-count driven.

`--adapter auto|generic|codex` selects event decoding; auto preserves the previous
mixed-input behavior. Adapter evidence capabilities live in `loopguard/core.py`:
Codex usage is available at turn completion, explicit progress is unknown;
generic events may supply interval usage and explicit progress. Process control
remains in the CLI, independent of decoding and detection. Cursor and DeepSeek
are future adapters, not supported clients. Missing evidence remains unknown.
