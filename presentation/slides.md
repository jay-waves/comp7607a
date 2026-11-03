<p class="eyebrow">COURSE PRESENTATION</p>

# LoopGuard

## Redirecting Stalled Agent Execution

Local-first monitoring · selective intervention · measurable tradeoffs

Notes:
This presentation describes an implemented monitoring method and a planned evaluation. Charts contain synthetic data; empirical effectiveness has not been established.

---

# Selective interruption under uncertainty

Can a lightweight monitor redirect stalled execution toward **useful progress**?

- Coding agents can repeat failed actions or revisit unchanged results.
- Fixed budgets limit cost, but cannot distinguish useful retries from waste.
- Selective interruption may save work and may also stop productive attempts.

Notes:
Evaluate the tradeoff rather than assuming every repetition is a loop.

---

# System scope

- Python CLI + SQLite; dependencies and execution managed with uv.
- Single-agent Codex tasks; Codex JSONL and a generic event schema.
- Compare intervention timing and actions under partial observability.
- Outside core scope: dashboards, fine-tuning, multi-agent coordination and a second full harness.

---

# Research objectives

1. Detect repeated tool outcomes under incomplete telemetry.
2. Quantify the resource–success tradeoff of selective interruption.
3. Assess transfer across agent environments with explicit adapter validation.

---

# Candidate agent environments

| Environment | Research role | LoopGuard status |
| --- | --- | --- |
| Codex | Primary evaluation harness | JSONL adapter implemented |
| DeepSeek Harness | Extensible runtime comparison | Candidate; adapter pending |
| Grok Build | Coding-agent comparison | Candidate; adapter pending |
| Cursor Agent CLI | Headless workflow comparison | Candidate; adapter pending |

Notes:
Core evaluation remains single-agent Codex. Candidates are an extension agenda, not implemented integrations or part of the initial pilot. Official descriptions: https://www.deepseek.com/harness/en/ ; https://x.ai/build ; https://cursor.com/docs/cli/overview . Telemetry, permissions and cancellation semantics require validation before comparison.

---

# System architecture

```mermaid
flowchart LR
  A[Codex / generic JSONL] --> B[Event adapter]
  B --> C[(Local SQLite)]
  B --> D[Repetition detector]
  D --> E[Intervention policy]
  D --> F[Optional decision API]
  F --> E
  G[Runtime limit] --> E
  E --> H[Warn / stop owned process]
  E --> C
```

Notes:
The tracer stores events and decisions locally. External inference is opt-in; only an explicitly launched child can be stopped. Unsupported metrics remain unknown.

---

# Operational definition of repetition

An identical **(tool, arguments, result, failed)** tuple occurs at least three times within the last sixteen completed tool events.

- Explicit progress clears the detection window.
- Matching uses normalized outcomes, not shortened display excerpts.
- Repetition is an observable proxy; it does not establish absence of progress.

Notes:
Legitimate polling and productive retries can satisfy the rule. The default threshold is configurable from 2 to 16.

---

# Observation comes first

- Default: record and warn; enforcement requires explicit configuration.
- Missing context / TPS measurements remain **unknown**.
- Silence alone is not evidence of wasted effort.
- Judge failure continues observation; the independent runtime limit remains active.

---

# Decision and fallback paths

```mermaid
flowchart LR
  A[Completed tool event] --> B{Repeated outcome?}
  B -->|No| O[Continue observation]
  B -->|Yes| C{Judge enabled?}
  C -->|No| P[Configured policy]
  C -->|Yes| J{Judge response}
  J -->|Failure / unknown| O
  J -->|Below threshold| O
  J -->|Stop probability ≥ 0.9| P
  P --> W[Default: warn]
  P --> R[Explicit: request stop]
  P --> S[Explicit: enforce on child]
```

Notes:
This diagram describes repetition-triggered intervention. The independent runtime limit is separate and remains active on judge failures. Missing metrics and silence never justify stopping.

---

# Evidence preparation pipeline

```mermaid
flowchart LR
  A[Latest 16 tool events] --> B[Normalize outcomes]
  B --> C[Group identical patterns]
  C --> D[Counts + evidence IDs]
  D --> E[Short excerpts]
  E --> F[Summary ≤ 6 KB]
  F --> G[Typed stop question]
  G --> H[Decision log]
```

Notes:
The window begins after explicit progress. Full normalized outcomes determine identity; excerpts do not. External excerpts are unredacted. The byte budget is not a token count. Up to eight calls per run are spaced by four tool events.

---

# Synthetic interaction demo

<!-- widget: observation -->

Notes:
Click three times to illustrate a warning. This counter does not implement the detector's tuple matching or window semantics. Reset restores the initial state.

---

# Decision APIs: cost and context

<!-- widget: decision -->

Notes:
Specifications checked 2026-11-03 against provider sources linked on the slide. Cloudflare's official blog reports $0.038/M and 24k hosted context; its model-reference page could not be retrieved. Jev has distinct request/question limits; opt-in long context is not enabled by LoopGuard. Qwen is free during preview. These are published specifications, not live integration results. All adapters still require live validation.

--- | --- |
| TypeSafe Jev | Mock-tested adapter |
| Cloudflare Clef-Flash | Mock-tested adapter |
| Qwen decision-model-preview | Request adapted; live response validation pending |

Same question and trace window across models.

**No authenticated model evaluation has been run.**

---

# Evidence and data boundaries

- External judge requests contain grouped counts, evidence IDs and short **unredacted excerpts**, within 6 KB.
- Raw traces remain local; summaries can omit relevant context.
- Review trace contents before sharing; source code and secrets may be present.
- Up to eight judge calls per run, spaced by four tool events.

Notes:
A separate judge token budget is future work. This public demo contains synthetic content only.

---

# Live monitoring sequence

```mermaid
sequenceDiagram
  participant A as Owned agent
  participant T as Tracer
  participant J as Optional judge
  participant P as Policy
  A->>T: Completed tool outcome
  T->>T: Record and detect repetition
  T->>J: Bounded evidence, if enabled
  Note over A: Child continues during judge call
  J-->>T: Stop probability or failure
  T->>P: Evidence and known decision
  P-->>A: Stop only with explicit enforcement
```

Notes:
The collector awaits the judge response while the child continues running. A response failure preserves observation. A timeout remains independent of the repetition policy.

---

# Experiment: when and how to intervene

| Stage | Hold fixed | Compare |
| --- | --- | --- |
| How | Trigger, model, initial effort | Continue; increase thinking; reduce thinking; restart context |
| When | Action selected on development tasks | No intervention; signal rules; rules + judge |

All attempts and judge calls share one total budget.

Notes:
This two-stage experiment is planned, not implemented. Select the action on separate development tasks and freeze it for the timing comparison.

---

# Planned intervention flow

```mermaid
flowchart LR
  O[Observe execution] --> T{Signal trigger?}
  T -->|No / unknown| C[Continue]
  T -->|Yes| G{Optional Jev gate?}
  G -->|Enabled| J{Confirm?}
  J -->|No / failure| C
  J -->|Yes| A{Assigned action}
  G -->|Disabled| A
  A --> H[Increase thinking]
  A --> L[Reduce thinking]
  A --> R[Restart context]
  A --> C
```

Notes:
These are experimental arms, not a learned action selector. Metric triggers, intervention judgment, effort controls and context restart are planned.

---

# Signals and restart

- Repetition, sustained TPS decline or abrupt context growth may trigger checks.
- Missing metrics remain unknown; signals alone do not prove failure.
- Restart keeps goal, code, failure summary and next hypothesis.
- Reasoning controls require model support; restart does not reset the budget.

Notes:
Current Codex telemetry does not supply reliable generation TPS or context snapshots. Do not infer context from cumulative usage or count tool waits as generation time.

---

# Tasks and measurements

| Task pair | Contrast |
| --- | --- |
| Service | Recovers / remains unavailable |
| Requirements | Consistent / contradictory |
| Code | Broken / already correct |

Measure task success and total cost, including judge and all attempts. Report recovery and harmful interventions; review blocker reports.

Notes:
Six configurations, three repetitions per condition. Calibrate on separate development variants and randomize condition order. Replay cannot establish outcomes after restart or thinking changes; fresh live runs are needed.

---

# Implementation and empirical status

- Implemented: event adapters, SQLite tracing, repetition rules and explicit interruption.
- Decision-model adapters have mock coverage; live inference remains unverified.
- Metric triggers, reasoning-effort controls and context restart are planned.
- Live agent evaluation has not been conducted.
- Resource savings and effects on task success remain **unknown**.

---

# Threats to validity

- False interruptions can damage otherwise successful work.
- Progress may be hidden and telemetry incomplete.
- Evidence summaries may omit important details.
- Conclusions apply only to the evaluated tasks and harness.

Notes:
The contribution is an empirical comparison under partial observability, not a universal guarantee of safe stopping.

---

# Conclusion

LoopGuard separates **observation**, **evidence assessment**, and **intervention** in agent execution.

- A local monitor makes repeated outcomes observable and replayable.
- Experiments separate intervention timing from intervention actions.
- Whether timely redirection improves success or reduces cost remains an empirical question.

---

# References

- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Project proposal](https://github.com/jay-waves/comp7607a/blob/main/PROPOSAL.md)
- [Provider configuration and CLI usage](https://github.com/jay-waves/comp7607a/blob/main/README.md)
- [Paul Tol colour schemes](https://sronpersonalpages.nl/~pault/)

<p class="eyebrow">PLANNED EXPERIMENTS · NO EMPIRICAL FINDINGS</p>
