"""End-to-end storage and supervisor checks, using only the Python standard library."""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

BIN = str(Path('target/debug/loopguard').resolve())

class Smoke(unittest.TestCase):
    def run_trace(self, *args, data=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db = str(Path(temp.name) / 'trace.sqlite')
        p = subprocess.run([BIN, '--db', db, '--run', 'test', *args],
                           input=data, text=True, capture_output=True, timeout=10)
        conn = sqlite3.connect(db)
        self.addCleanup(conn.close)
        return p, conn

    def test_decision_http(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                requests[-1]['received_auth'] = self.headers.get('Authorization')
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(self.server.reply).encode())
            def log_message(self, *args): pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        old = os.environ.get('LOOPGUARD_DECISION_KEY')
        os.environ['LOOPGUARD_DECISION_KEY'] = 'mock-key'
        def restore():
            if old is None: os.environ.pop('LOOPGUARD_DECISION_KEY', None)
            else: os.environ['LOOPGUARD_DECISION_KEY'] = old
        self.addCleanup(restore)
        for reply, action in [
            ({'answers': {'stop': {'type': 'noul', 'noul': 0.95}}}, 'stop'),
            ({'success': True, 'result': {'answers': {'stop': {'type': 'noul', 'noul': 0.2}}}}, 'continue'),
            ({'answers': {'stop': {'type': 'noul', 'noul': 'invalid'}}}, 'continue')]:
            server.reply = reply
            p, _ = self.run_trace('--request-stop', '--decision-url',
                                 f'http://127.0.0.1:{server.server_port}',
                                 data=Path('examples/loop.jsonl').read_text())
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout.splitlines()[-1])['decision']['action'], action)
        self.assertEqual(len(requests), 3)
        self.assertEqual(requests[0]['questions']['stop']['type'], 'noul')
        self.assertEqual(requests[0]['received_auth'], 'Bearer mock-key')
        server.reply = {'answers': {'stop': {'type': 'noul', 'noul': 0.95}}}
        p, _ = self.run_trace('--decision-auth', 'raw', '--decision-model', 'decision-model-preview',
                             '--decision-url', f'http://127.0.0.1:{server.server_port}',
                             data=Path('examples/loop.jsonl').read_text())
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(requests[-1]['received_auth'], 'mock-key')
        self.assertEqual(requests[-1]['model'], 'decision-model-preview')
        self.assertEqual(json.loads(p.stdout.splitlines()[-1])['decision']['action'], 'warn')


    def test_replay_and_storage(self):
        p, db = self.run_trace(data=Path('examples/loop.jsonl').read_text())
        self.assertEqual(p.returncode, 0, p.stderr)
        events = [json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(events[-1]['decision']['action'], 'warn')
        self.assertEqual(events[1]['decision']['generation_tps'], 50)
        self.assertEqual(db.execute('select count(*) from events').fetchone()[0], 4)

    def test_stop_child(self):
        p, db = self.run_trace('--enforce', '--command', 'python3', 'examples/fake_agent.py')
        self.assertEqual(p.returncode, 2, p.stderr)
        summary = json.loads(db.execute('select summary from summaries').fetchone()[0])
        self.assertTrue(summary['interrupted'])
        self.assertEqual(summary['tool_calls'], 3)

    def test_timeout_without_events(self):
        p, _ = self.run_trace('--timeout-secs', '1', '--command', 'python3', '-c', 'import time; time.sleep(20)')
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual(json.loads(p.stderr)['reason'], 'hard_timeout')

    def test_malformed_and_unknown_events(self):
        p, db = self.run_trace(data='broken\n{"type":"future.event"}\n')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(db.execute('select count(*) from events').fetchone()[0], 2)
        self.assertIn('parse_error', json.loads(p.stdout.splitlines()[0])['decision'])

    def test_child_failure(self):
        p, _ = self.run_trace('--command', 'python3', '-c', 'raise SystemExit(7)')
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stderr)['child_exit_code'], 7)

if __name__ == '__main__':
    unittest.main()
