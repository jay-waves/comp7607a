# Minimal comparison plan

Status: design only; no agent experiments or model comparisons have been run. Local synthetic checks validate software behavior, not detection quality.

## Questions and conditions

Does selective intervention save resources without stopping productive work? Does a judge improve on cheap repetition rules enough to justify its own cost?

| Condition | Trigger | Decision | Availability |
| --- | --- | --- | --- |
| A: Budget only | Fixed runtime/token limit | Stop at budget | Runtime limit implemented; token enforcement deferred |
| B: Rules | Repeated unchanged tool outcomes | Stop at threshold | Implemented |
| C: Selective judge | Same rules as B | Judge chooses continue or stop | Typed API adapter implemented; provider evaluation pending |

Use the same underlying agent, harness version, permissions, task prompt, runtime limit, and model configuration in each condition. Condition A should run in observation mode so its trace is collected without repetition enforcement. Judge timeout/error falls back to continue; the independent budget remains active.

## Small dataset and stages

1. Start with six development tasks: two ordinary coding tasks, two injected unproductive behaviors, one legitimate polling/retry task, and one slow successful command. Use these only to debug instrumentation and set thresholds.
2. Freeze thresholds and prompts before testing twelve held-out tasks (four per group: ordinary, unproductive, legitimate slow/retry). Use different repositories or task families to limit leakage. Run each condition three times per task: 108 runs for A/B/C, or 72 for the initial A/B comparison.
3. For a larger final study, expand to the proposal's 8 development / 16 held-out design. The smaller pilot is intended to expose failure modes, not establish statistical non-inferiority.

Each task needs a clean repository snapshot, a written objective, an executable success check, an expected progress signal, and a fixed budget. Failure injections may include an unavailable dependency, repeated unchanged test failures, and alternating searches that return the same result. Include actual autonomous trajectories; fabricated repeated JSON lines are implementation fixtures only.

## Labels and measurements

Annotators inspect baseline traces without seeing policy outputs. Label suspicious segments as productive, unproductive, or uncertain, with the earliest defensible intervention event. Two independent annotators resolve disagreements and report agreement; exclude uncertain labels from primary detection metrics and report their count. Repeated output alone is insufficient evidence of uselessness.

Record task success, total input/output tokens, wall time, tool calls, stop event, actual child termination, and judge tokens/latency. Report cached token usage separately if available; do not estimate dollars without a documented price schedule. Missing TPS or context measurements remain missing. Model-judge cost belongs in the intervention condition's total.

Primary comparisons are success-rate change and resource expenditure. Report both overall results and the unproductive subset; do not claim savings merely because failed runs finish sooner. Include false interventions on negative controls, precision/recall against annotations, and delay from the annotated intervention point. Show per-task results and paired task-level bootstrap confidence intervals. Pair repeated runs by task and configuration, recognizing that model sampling prevents exact counterfactual matching.

Replay baseline traces first to inspect detector thresholds and labels. Then run live interventions on fresh task snapshots: replay cannot establish realized savings, preserved success, or cancellation reliability. Randomize condition order to reduce service-time effects.

## Optional ablations, in priority order

- Repetition threshold: 2, 3, or 4, calibrated only on development tasks.
- Judge input: last 8 tool events plus a compact summary versus last 32 events, with explicit token caps and identical judge configuration.
- Judge model: TypeSafe Jev versus Clef-Flash versus Qwen decision-model-preview, using the same input and decision schema.

The prototype permits at most eight judge calls per run, spaced by four completed tool events. A separate judge-token budget is not implemented. Freeze limits before held-out testing. Defer fine-tuning and second-harness evaluation unless the core comparison is complete.

## Result template

| Policy | Success / runs | Median total tokens | Median seconds | False stops | Judge tokens | Cancellation failures |
| --- | --- | --- | --- | --- | --- | --- |
| A | TBD | TBD | TBD | N/A | 0 | TBD |
| B | TBD | TBD | TBD | TBD | 0 | TBD |
| C | TBD | TBD | TBD | TBD | TBD | TBD |

Keep traces, task manifests, version identifiers, prompts, and decision logs together. Report all exclusions and infrastructure failures. The proposal's 20% waste reduction / at most 5-point success reduction is an exploratory target, not a promised finding.
