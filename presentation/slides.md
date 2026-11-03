<p class="eyebrow">COURSE PROJECT · PROPOSAL DEMO</p>

# LoopGuard

## Detecting Unproductive Agent Execution

Local-first monitoring · selective intervention · measurable tradeoffs

Notes:
Proposal demonstration. No authenticated model evaluation or held-out experiments have been run.

---

# Research question

Can a lightweight monitor reduce wasted agent execution **without harming task success**?

- Coding agents can repeat failed actions or revisit unchanged results.
- Fixed budgets limit cost, but cannot distinguish useful retries from waste.
- Selective interruption may save work and may also stop productive attempts.

Notes:
Evaluate the tradeoff rather than assuming every repetition is a loop.

---

# Scope and design

- Python CLI + SQLite; dependencies and execution managed with uv.
- Single-agent Codex tasks; Codex JSONL and a generic event schema.
- Compare interruption policies under partial observability.
- Outside core scope: dashboards, fine-tuning, multi-agent coordination and a second full harness.

---

# From events to intervention

<div class="pipeline" aria-label="LoopGuard architecture">
  <div class="panel"><h2>Record</h2><p>Codex / generic JSONL</p><p>Python tracer → SQLite</p></div>
  <div class="panel"><h2>Assess</h2><p>Repetition rules</p><p>Optional decision API</p></div>
  <div class="panel"><h2>Act</h2><p>Policy + runtime limit</p><p>Warn or stop owned process</p></div>
</div>

Stored events and decisions support replay and evaluation.

Notes:
Flow follows the architecture in PROPOSAL.md. The presentation is a static frontend, not a monitoring dashboard.

---

# Observation comes first

- Default: record and warn; enforcement requires explicit configuration.
- Missing context / TPS measurements remain **unknown**.
- Silence alone is not evidence of wasted effort.
- Judge failure continues observation; the independent runtime limit remains active.

---

# Synthetic interaction demo

<!-- widget: observation -->

Notes:
Click three times to illustrate a warning. This counter does not implement the detector's tuple matching or window semantics. Reset restores the initial state.

---

# Optional decision models

| Model | Current verification |
| --- | --- |
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

# Experiments: three conditions

| Condition | Intervention policy |
| --- | --- |
| A · Budget | Stop only at runtime limit |
| B · Rules | Budget + repetition-based interruption |
| C · Decision model | Budget + model-confirmed repetition interruption |

Replay evaluates detection. Fresh live runs measure realized savings.

---

# Dataset and controls

- Calibrate on **6 development tasks**, then freeze settings.
- Evaluate **12 held-out tasks × 3 runs × 3 conditions = 108 runs** for one judge model.
- A/B pilot: 72 runs. Each additional judge model: 36 runs.
- Include coding, loops, legitimate retries and slow successful operations.

Notes:
Fix agent, prompts, permissions and budgets; reset repository snapshots, use executable success checks and randomize condition order.

---

# Measurements and ground truth

| Measure | Purpose |
| --- | --- |
| Task success / false stops | Harm to productive work |
| Tokens / time / tool calls | Savings including judge overhead |
| Precision / recall / delay | Agreement with annotated segments |
| Cancellation failures | Whether interruption takes effect |

Two annotators label baseline segments and earliest defensible intervention.

Notes:
Report agreement and uncertain labels. Judge predictions are not ground truth. Report per-task results and task-level bootstrap intervals; runs are imperfect counterfactuals.

---

# Exploratory target, not a result

## 20% fewer median tokens on unproductive runs

With at most a **5 percentage point** drop in overall success.

- Small samples cannot establish statistical non-inferiority.
- Ablations may vary repetition thresholds, summary budgets and judge models.
- **Experiments have not been run; savings and success effects are unknown.**

---

# Token use across policies

<!-- widget: tokens -->

Notes:
Fabricated values: A 40k, B 26k, C 31k. These are layout fixtures, not findings or a forecast.

---

# Success and interruption tradeoffs

<!-- widget: quality -->

Notes:
Fabricated percentages; no sample size or confidence interval is claimed. Success and false-stop rates are separate illustrative metrics.

---

# When repeated effort ends

<!-- widget: timeline -->

Notes:
Synthetic trajectories flatten when the illustrative policy stops tool execution. They are not replay traces.

---

# Deliverables and schedule

| Stage | Deliverable |
| --- | --- |
| Weeks 1–2 | Tracer, SQLite, rules, interruption, tests |
| Week 3 | Live API validation and development calibration |
| Week 4 | Held-out experiments, ablations, failure analysis |

Implemented: prototype and cross-platform CI/release workflows.

Outstanding: live provider validation, evaluation tasks and results.

---

# Risks and limits

- False interruptions can damage otherwise successful work.
- Progress may be hidden and telemetry incomplete.
- Evidence summaries may omit important details.
- Conclusions apply only to the evaluated tasks and harness.

Notes:
The contribution is an empirical comparison under partial observability, not a universal guarantee of safe stopping.

---

# References

- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Project proposal](https://github.com/jay-waves/comp7607a/blob/main/PROPOSAL.md)
- [Provider configuration and CLI usage](https://github.com/jay-waves/comp7607a/blob/main/README.md)
- [Paul Tol colour schemes](https://sronpersonalpages.nl/~pault/)

<p class="eyebrow">PROPOSAL DEMO · NO MEASURED RESULTS</p>
