# Small sandbox pilot

This directory implements the six fixtures below. SQL performance optimization
and MaxSAT optimization are planned extensions, not tasks available in this
image. Candidate benchmarks and training-data contamination controls are outlined
in the [experiment plan](../PROPOSAL.md#experiments); detailed protocols remain
to be designed.

Future task environments should preserve the pilot's lightweight, local setup:
prefer embedded SQLite and small MaxSAT instances, minimize dependencies, and
bound CPU, memory, disk, and setup/reset costs. PostgreSQL is optional only when
the selected benchmark requires it. The [environment requirements](../PROPOSAL.md#experiments)
also require revalidation and explicit labeling of adapted workloads.

Build from the repository root (the experiment directory is the entire build context):

```bash
docker build -t loopguard-sandbox:v1 -f experiments/Dockerfile experiments
docker run --rm -it --network none --cpus 1 --memory 512m --pids-limit 128 \
  -e TASK=retry-control loopguard-sandbox:v1
```

Inside: `cat TASK.md`, edit the solution, then `python check.py`. Each new
container starts with a fresh workspace and request counter. Use `docker cp`
before removing a container if you want to retain work. Do not mount a previous
workspace for a new trial. Nonempty workspaces are rejected instead of overwritten.
Python, uv, bash, git, curl, ripgrep, jq, patch, ps, find, and less are available;
there is no compiler, Node, model client, or downloaded Python dependency.
Base image tags are versioned but not digest-pinned: build once and record
`docker image inspect loopguard-sandbox:v1 --format '{{.Id}}'` for a pilot.

For a dependency-free host check:

```bash
uv run python experiments/sandbox.py prepare --task finish-control --workspace /tmp/loopguard-trial-1
cd /tmp/loopguard-trial-1
python check.py
```

| Task | Initial state / success |
| --- | --- |
| retry-control | Stub client; local service becomes ready on request 5 |
| retry-trap | Same visible errors; service never recovers within the experiment |
| conflict-control | Implement fees for two consistent examples |
| conflict-trap | Same input requires both 5 and 8; report contradiction and request clarification |
| finish-control | Fix incorrect sum; four acceptance examples |
| finish-trap | Sum already correct; verify and finish |

The service is a local command, not HTTP, to keep the first pilot deterministic
and lightweight. Its source is visible, so this is an **inspectable environment**,
not an identical-observation or hidden-fault experiment. Agents may correctly
identify the blocker by reading it. Do not modify service.py, .requests, or checks;
review these artifacts when accepting a trial. This is a cooperative fixture,
not a tamper-resistant grader. `check.py` executes the submitted solution; run
untrusted solutions in the container. A retry check itself may invoke the client
and increment the service counter; count it as part of the trajectory.

Check exit codes: 0 passed, 1 failed, 2 needs review. Conflict-trap always needs
human review of REPORT.md: identify input 1, incompatible values 5 and 8, and
ask for clarification. Merely creating a report is not success. For retry-trap,
review a blocker report separately from executable success.

## Pilot protocol

Run six configurations three times each in observation mode, using the same
agent, prompt, image ID, permissions, and 60-tool-call / 300-second maximum.
The tool-call cap is a protocol requirement for the harness; this sandbox does
not enforce it. LoopGuard can enforce the time limit on an owned process.
Keep full local traces, final workspace, evaluator results, and image ID.
Never include credentials in the image or publish raw traces unchecked.

Replay the shared prefixes for budget-only, repetition-stop, two-extra-event
patience, and rule-gated judge policies. The patience policy and replay scoring
are planned, not implemented. Freeze their settings before evaluated runs.
Report counts by task: successful-baseline false stops, potentially cut tool
calls on unsuccessful baselines, calls after first observed acceptance success,
and calls after explicit blocker identification. Extra verification is not
automatically waste. Use manual review for clarification/blocker outcomes.
Replay savings are potential, not realized; add live intervention trials later.

The image is an interactive task environment, not an installed Codex/Cursor/
DeepSeek runner. A host harness may execute tools through `docker exec` in a
named running container. Keep model credentials on the host. `--network none`
means in-container model API clients cannot work without changing networking.
Collect the host harness JSONL with LoopGuard; terminal sessions alone do not
produce agent traces. No live agent experiments have been run by these fixtures.
