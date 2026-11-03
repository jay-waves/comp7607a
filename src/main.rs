mod decision;
use anyhow::{bail, Context, Result};
use clap::Parser;
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::VecDeque,
    io::{self, BufRead},
    time::{SystemTime, UNIX_EPOCH},
};

/// Record generic or Codex JSONL; emit advisory decisions for a supervising harness.
#[derive(Parser)]
struct Args {
    /// Opt-in external typed decision endpoint; sends bounded trace content.
    #[arg(long)]
    decision_url: Option<String>,
    #[arg(long, default_value = "clef-flash")]
    decision_model: String,
    /// Authorization header format; Qwen's documented example uses raw.
    #[arg(long, default_value = "bearer", value_parser = ["bearer", "raw"])]
    decision_auth: String,
    #[arg(long, default_value = "trace.sqlite")]
    db: String,
    /// Unique run ID. Reusing a run is rejected to prevent mixed detector state.
    #[arg(long)]
    run: String,
    #[arg(long, default_value_t = 3)]
    repeats: usize,
    /// Emit stop requests instead of warnings. The caller must enforce them.
    #[arg(long)]
    request_stop: bool,
    /// Enforce repetition decisions for a child command (requires --command).
    #[arg(long, requires = "command")]
    enforce: bool,
    /// Hard runtime budget for a child; independent of detector decisions.
    #[arg(long, default_value_t = 300)]
    timeout_secs: u64,
    /// Launch a JSONL-producing harness. All remaining arguments belong to it.
    #[arg(long, num_args = 1.., trailing_var_arg = true, allow_hyphen_values = true)]
    command: Vec<String>,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Event {
    kind: String,
    tool: Option<String>,
    arguments: Option<Value>,
    result: Option<Value>,
    failed: Option<bool>,
    /// Explicit harness evidence of progress resets the repetition window.
    progress: Option<bool>,
    input_tokens: Option<u64>,
    output_tokens: Option<u64>,
    context_tokens: Option<u64>,
    generation_ms: Option<u64>,
    gap_ms: Option<u64>,
}

fn normalize(v: &Value) -> Result<Option<Event>> {
    if v.get("kind").is_some() {
        return Ok(Some(serde_json::from_value(v.clone())?));
    }
    match v["type"].as_str() {
        Some("item.completed") => {
            let i = &v["item"];
            let tool = i["type"].as_str().unwrap_or("");
            if !matches!(tool, "command_execution" | "mcp_tool_call") {
                return Ok(None);
            }
            Ok(Some(Event {
                kind: "tool_end".into(),
                tool: Some(if tool == "mcp_tool_call" {
                    format!(
                        "{}:{}",
                        i["server"].as_str().unwrap_or(""),
                        i["tool"].as_str().unwrap_or("")
                    )
                } else {
                    tool.into()
                }),
                arguments: Some(if tool == "command_execution" {
                    i["command"].clone()
                } else {
                    i["arguments"].clone()
                }),
                result: Some(if tool == "command_execution" {
                    i["aggregated_output"].clone()
                } else if i["result"].is_null() && i["error"].is_null() {
                    Value::Null
                } else {
                    json!({"result":i["result"],"error":i["error"]})
                }),
                failed: Some(
                    i["exit_code"].as_i64().is_some_and(|c| c != 0) || i["status"] == "failed",
                ),
                ..Default::default()
            }))
        }
        Some("turn.completed") => Ok(Some(Event {
            kind: "usage".into(),
            input_tokens: v["usage"]["input_tokens"].as_u64(),
            output_tokens: v["usage"]["output_tokens"].as_u64(),
            ..Default::default()
        })),
        Some(_) => Ok(None), // Preserve unknown Codex events without inventing measurements.
        None => bail!("expected generic kind or Codex type"),
    }
}

#[derive(Default)]
struct Detector {
    recent: VecDeque<String>,
}
impl Detector {
    fn observe(&mut self, e: &Event, threshold: usize) -> Option<&'static str> {
        if e.progress == Some(true) {
            self.recent.clear();
            return None;
        }
        if e.kind != "tool_end" {
            return None;
        }
        // Require actual arguments and output; missing evidence is not a repeat.
        let (Some(tool), Some(args), Some(result)) = (&e.tool, &e.arguments, &e.result) else {
            return None;
        };
        if args.is_null() || result.is_null() {
            return None;
        }
        let key = json!([tool, args, result, e.failed]).to_string();
        self.recent.push_back(key.clone());
        if self.recent.len() > 16 {
            self.recent.pop_front();
        }
        (self.recent.iter().filter(|x| **x == key).count() >= threshold)
            .then_some("repeated_tool_arguments_and_result")
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    if !(2..=16).contains(&args.repeats) {
        bail!("--repeats must be between 2 and 16");
    }
    let db = Connection::open(&args.db)?;
    db.execute_batch("PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS summaries(run TEXT PRIMARY KEY, summary TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, started_ms INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS events(run TEXT NOT NULL, seq INTEGER NOT NULL, received_ms INTEGER NOT NULL, raw TEXT NOT NULL, normalized TEXT, decision TEXT NOT NULL, PRIMARY KEY(run,seq));")?;
    let now = || {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as i64
    };
    db.execute("INSERT INTO runs VALUES (?1,?2)", params![args.run, now()])
        .context("run ID must be unique")?;
    let mut child = if args.command.is_empty() {
        None
    } else {
        let mut command = std::process::Command::new(&args.command[0]);
        command
            .args(&args.command[1..])
            .stdout(std::process::Stdio::piped());
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            command.process_group(0);
        }
        Some(OwnedChild(command.spawn().context("launch harness")?))
    };
    let reader: Box<dyn BufRead + Send> = match child.as_mut() {
        Some(c) => Box::new(io::BufReader::new(c.0.stdout.take().unwrap())),
        None => Box::new(io::BufReader::new(io::stdin())),
    };
    let (tx, rx) = std::sync::mpsc::sync_channel(32);
    std::thread::spawn(move || {
        for line in reader.lines() {
            if tx.send(line).is_err() {
                break;
            }
        }
    });
    let started = std::time::Instant::now();
    let mut detector = Detector::default();
    let mut seq = 0i64;
    let mut tool_calls = 0;
    let mut input_tokens = 0u64;
    let mut output_tokens = 0u64;
    let mut context_tokens = None;
    let intervention_action = if args.request_stop || args.enforce {
        "stop"
    } else {
        "warn"
    };
    let mut judge_calls = 0;
    let mut last_judge = None;
    let mut history = VecDeque::new();
    let mut interrupted = false;
    let mut interrupt_reason = None;
    loop {
        if child.is_some() && started.elapsed().as_secs() >= args.timeout_secs {
            interrupted = true;
            interrupt_reason = Some("hard_timeout");
            break;
        }
        let line = match rx.recv_timeout(std::time::Duration::from_millis(100)) {
            Ok(line) => line?,
            Err(std::sync::mpsc::RecvTimeoutError::Timeout) => continue,
            Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => {
                if let Some(c) = child.as_mut() {
                    if c.0.try_wait()?.is_none() {
                        std::thread::sleep(std::time::Duration::from_millis(100));
                        continue;
                    }
                }
                break;
            }
        };
        let parsed = serde_json::from_str::<Value>(&line)
            .map_err(anyhow::Error::from)
            .and_then(|v| normalize(&v));
        let (normalized, mut decision) = match parsed {
            Ok(e) => {
                let reason = e.as_ref().and_then(|e| detector.observe(e, args.repeats));
                let tps = e
                    .as_ref()
                    .and_then(|e| match (e.output_tokens, e.generation_ms) {
                        (Some(t), Some(ms)) if ms > 0 => Some(t as f64 * 1000.0 / ms as f64),
                        _ => None,
                    });
                let stall = e
                    .as_ref()
                    .and_then(|e| e.gap_ms)
                    .is_some_and(|ms| ms >= 30_000);
                (
                    e,
                    json!({"action": if reason.is_some() { intervention_action } else {"continue"}, "reason":reason, "generation_tps":tps, "stall_observed":stall}),
                )
            }
            Err(err) => (
                None,
                json!({"action":"continue", "parse_error":err.to_string()}),
            ),
        };
        if let Some(e) = &normalized {
            history.push_back(json!({"seq":seq,"event":serde_json::to_string(e)?.chars().take(2000).collect::<String>()}));
            if history.len() > 8 {
                history.pop_front();
            }
        }
        if let Some(url) = &args.decision_url {
            if !decision["reason"].is_null() {
                decision["action"] = json!("continue");
                if judge_calls < 8 && last_judge.is_none_or(|n| tool_calls >= n + 4) {
                    judge_calls += 1;
                    last_judge = Some(tool_calls);
                    let timeout = if child.is_some() {
                        std::time::Duration::from_secs(args.timeout_secs)
                            .saturating_sub(started.elapsed())
                            .min(std::time::Duration::from_secs(3))
                    } else {
                        std::time::Duration::from_secs(3)
                    };
                    let t = std::time::Instant::now();
                    match decision::call(
                        url,
                        &args.decision_model,
                        &args.decision_auth,
                        json!(history),
                        timeout,
                    ) {
                        Ok((stop, result)) => {
                            if stop {
                                decision["action"] = json!(intervention_action);
                            }
                            decision["judge"] = result;
                        }
                        Err(_) => {
                            decision["judge_error"] = json!("request_failed_or_invalid_response");
                        }
                    }
                    decision["judge_ms"] = json!(t.elapsed().as_millis());
                } else {
                    decision["judge_skipped"] = json!("cooldown_or_call_budget");
                }
            }
        }
        if normalized.as_ref().is_some_and(|e| e.kind == "tool_end") {
            tool_calls += 1;
        }
        if let Some(e) = &normalized {
            input_tokens = input_tokens.saturating_add(e.input_tokens.unwrap_or(0));
            output_tokens = output_tokens.saturating_add(e.output_tokens.unwrap_or(0));
            if e.context_tokens.is_some() {
                context_tokens = e.context_tokens;
            }
        }
        db.execute(
            "INSERT INTO events VALUES (?1,?2,?3,?4,?5,?6)",
            params![
                args.run,
                seq,
                now(),
                line,
                normalized.map(|e| serde_json::to_string(&e)).transpose()?,
                decision.to_string()
            ],
        )?;
        println!("{}", json!({"run":args.run,"seq":seq,"decision":decision}));
        seq += 1;
        if args.enforce && decision["action"] == "stop" {
            interrupted = true;
            interrupt_reason = Some("repetition");
            break;
        }
    }
    let status = if let Some(c) = child.as_mut() {
        if interrupted {
            c.terminate()?;
        }
        Some(c.0.wait()?)
    } else {
        None
    };
    let summary = json!({"events":seq,"tool_calls":tool_calls,"input_tokens":input_tokens,"output_tokens":output_tokens,"last_context_tokens":context_tokens,"interrupted":interrupted,
        "reason":interrupt_reason,"child_exit_code":status.and_then(|s| s.code()),
        "elapsed_ms":started.elapsed().as_millis()});
    db.execute(
        "INSERT INTO summaries VALUES (?1,?2)",
        params![args.run, summary.to_string()],
    )?;
    eprintln!("{summary}");
    if interrupted {
        std::process::exit(2);
    }
    if status.is_some_and(|s| !s.success()) {
        std::process::exit(1);
    }
    Ok(())
}

// Never leave an owned harness running on a recording error.
struct OwnedChild(std::process::Child);
impl OwnedChild {
    fn terminate(&mut self) -> Result<()> {
        #[cfg(unix)]
        {
            let result = unsafe { libc::kill(-(self.0.id() as i32), libc::SIGKILL) };
            if result != 0 && io::Error::last_os_error().raw_os_error() != Some(libc::ESRCH) {
                return Err(io::Error::last_os_error().into());
            }
        }
        #[cfg(not(unix))]
        if self.0.try_wait()?.is_none() {
            self.0.kill()?;
        }
        Ok(())
    }
}
impl Drop for OwnedChild {
    fn drop(&mut self) {
        let _ = self.terminate();
        let _ = self.0.wait();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn event(result: &str) -> Event {
        serde_json::from_value(json!({"kind":"tool_end","tool":"shell","arguments":"test","result":result,"failed":true})).unwrap()
    }
    #[test]
    fn detects_cycle_and_resets_on_progress() {
        let mut d = Detector::default();
        for _ in 0..2 {
            assert!(d.observe(&event("A"), 3).is_none());
            assert!(d.observe(&event("B"), 3).is_none());
        }
        assert!(d.observe(&event("A"), 3).is_some());
        d.observe(
            &Event {
                progress: Some(true),
                ..Default::default()
            },
            3,
        );
        assert!(d.observe(&event("A"), 3).is_none());
    }
    #[test]
    fn changing_output_is_not_a_loop() {
        let mut d = Detector::default();
        for i in 0..30 {
            assert!(d.observe(&event(&i.to_string()), 3).is_none());
        }
    }
    #[test]
    fn missing_mcp_result_does_not_trigger() {
        let e = normalize(&json!({"type":"item.completed","item":{"type":"mcp_tool_call","tool":"query","server":"local","arguments":{}}})).unwrap().unwrap();
        let mut d = Detector::default();
        for _ in 0..4 {
            assert!(d.observe(&e, 3).is_none());
        }
    }
    #[test]
    fn codex_usage_is_not_context_or_tps() {
        let e = normalize(
            &json!({"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":20}}),
        )
        .unwrap()
        .unwrap();
        assert_eq!(e.input_tokens, Some(100));
        assert_eq!(e.context_tokens, None);
        assert_eq!(e.generation_ms, None);
    }
}
