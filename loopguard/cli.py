"""JSONL collector and optional child-process supervisor."""
import argparse
import json
import os
import queue
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from .core import Detector, normalize
from .decision import call
from .summary import TraceSummary


def terminate(child):
    if os.name == 'posix':
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif child.poll() is None:
        child.kill()
    child.wait()


def run(args):
    db = sqlite3.connect(args.db)
    child = None
    try:
        db.executescript('''PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, started_ms INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS events(run TEXT, seq INTEGER, received_ms INTEGER, raw TEXT, normalized TEXT, decision TEXT, PRIMARY KEY(run,seq));
        CREATE TABLE IF NOT EXISTS summaries(run TEXT PRIMARY KEY, summary TEXT NOT NULL);''')
        db.execute('INSERT INTO runs VALUES (?,?)', (args.run, int(time.time()*1000)))
        db.commit()
        if args.command:
            child = subprocess.Popen(args.command, stdout=subprocess.PIPE, text=True, encoding='utf-8', start_new_session=os.name == 'posix')
        source = child.stdout if child else sys.stdin
        lines = queue.Queue(maxsize=32)

        def read():
            try:
                for line in source:
                    lines.put(line.rstrip('\r\n'))
            except Exception as exc:
                lines.put(exc)
            finally:
                lines.put(None)

        threading.Thread(target=read, daemon=True).start()
        started = time.monotonic()
        detector, history = Detector(args.repeats), TraceSummary()
        seq = tools = inputs = outputs = judge_calls = 0
        context = last_judge = reason = None
        eof = False
        action = 'stop' if args.enforce or args.request_stop else 'warn'
        while True:
            if child and time.monotonic()-started >= args.timeout_secs:
                reason = 'hard_timeout'
                break
            if eof:
                if child and child.poll() is None:
                    time.sleep(.1)
                    continue
                break
            try:
                line = lines.get(timeout=.1)
            except queue.Empty:
                continue
            if line is None:
                eof = True
                continue
            if isinstance(line, Exception):
                raise line
            event = None
            try:
                event = normalize(json.loads(line))
                trigger = detector.observe(event) if event else None
                e = event or {}
                tps = e['output_tokens']*1000/e['generation_ms'] if e.get('output_tokens') is not None and e.get('generation_ms') else None
                decision = dict(action=action if trigger else 'continue', reason=trigger, generation_tps=tps, stall_observed=(e.get('gap_ms') or 0) >= 30000)
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                decision = dict(action='continue', parse_error=str(exc))
            if event:
                history.observe(seq, event)
            if args.decision_url and decision.get('reason'):
                decision['action'] = 'continue'
                if judge_calls < 8 and (last_judge is None or tools >= last_judge+4):
                    judge_calls += 1
                    last_judge = tools
                    t = time.monotonic()
                    timeout = min(3, args.timeout_secs-(t-started)) if child else 3
                    try:
                        if timeout <= 0:
                            raise ValueError('budget exhausted')
                        state = history.build(decision["reason"])
                        decision["judge_input"] = state
                        stop, result = call(args.decision_url, args.decision_model, args.decision_auth, state, timeout)
                        decision['judge'] = result
                        if stop:
                            decision['action'] = action
                    except Exception:
                        decision['judge_error'] = 'request_failed_or_invalid_response'
                    decision['judge_ms'] = int((time.monotonic()-t)*1000)
                else:
                    decision['judge_skipped'] = 'cooldown_or_call_budget'
            if event:
                tools += event['kind'] == 'tool_end'
                inputs += event.get('input_tokens') or 0
                outputs += event.get('output_tokens') or 0
                if event.get('context_tokens') is not None:
                    context = event['context_tokens']
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?)', (args.run, seq, int(time.time()*1000), line, json.dumps(event) if event else None, json.dumps(decision)))
            db.commit()
            print(json.dumps(dict(run=args.run, seq=seq, decision=decision)), flush=True)
            seq += 1
            if args.enforce and decision['action'] == 'stop':
                reason = 'repetition'
                break
        if child and reason:
            terminate(child)
        status = child.wait() if child else None
        summary = dict(events=seq, tool_calls=tools, input_tokens=inputs, output_tokens=outputs, last_context_tokens=context, interrupted=reason is not None, reason=reason, child_exit_code=status, elapsed_ms=int((time.monotonic()-started)*1000))
        db.execute('INSERT INTO summaries VALUES (?,?)', (args.run, json.dumps(summary)))
        db.commit()
        print(json.dumps(summary), file=sys.stderr)
        return 2 if reason else (1 if status else 0)
    finally:
        if child:
            terminate(child)
            child.stdout.close()
        db.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True)
    p.add_argument('--db', default='trace.sqlite')
    p.add_argument('--repeats', type=int, choices=range(2,17), default=3)
    p.add_argument('--request-stop', action='store_true')
    p.add_argument('--enforce', action='store_true')
    p.add_argument('--timeout-secs', type=float, default=300)
    p.add_argument('--decision-url')
    p.add_argument('--decision-model', default='clef-flash')
    p.add_argument('--decision-auth', choices=['bearer','raw'], default='bearer')
    p.add_argument('--command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    if args.enforce and not args.command:
        p.error('--enforce requires --command')
    if args.timeout_secs <= 0:
        p.error('--timeout-secs must be positive')
    try:
        return run(args)
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
