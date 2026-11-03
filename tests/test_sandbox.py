"""Acceptance and reset behavior for the small experiment fixtures."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from loopguard.core import normalize

spec = importlib.util.spec_from_file_location('sandbox', Path(__file__).resolve().parents[1] / 'experiments' / 'sandbox.py')
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)


class SandboxTests(unittest.TestCase):
    def test_explicit_adapters(self):
        with self.assertRaises(ValueError):
            normalize({'type': 'turn.completed'}, 'generic')
        with self.assertRaises(ValueError):
            normalize({'kind': 'tool_end'}, 'codex')
        self.assertEqual(normalize({'type': 'turn.completed', 'usage': {'output_tokens': 3}}, 'codex')['output_tokens'], 3)

    def test_all_tasks_and_reset(self):
        for task in sandbox.TASKS:
            with self.subTest(task=task), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                sandbox.prepare(root, task)
                with self.assertRaises(ValueError):
                    sandbox.prepare(root, task)
                expected = 'needs_review' if task == 'conflict-trap' else 'passed' if task == 'finish-trap' else 'failed'
                self.assertEqual(sandbox.check(root, task)['status'], expected)
                if task.startswith('finish'):
                    (root / 'solution.py').write_text('def total(values):\n    return sum(values)\n')
                    self.assertEqual(sandbox.check(root, task)['status'], 'passed')
                if task == 'conflict-control':
                    (root / 'solution.py').write_text('def fee(weight):\n    return {1: 5, 2: 8}[weight]\n')
                    self.assertEqual(sandbox.check(root, task)['status'], 'passed')

    def test_recovery_is_call_based_and_resets(self):
        for task in ('retry-control', 'retry-trap'):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                sandbox.prepare(root, task)
                for attempt in range(1, 7):
                    result = subprocess.run([sys.executable, 'service.py'], cwd=root, capture_output=True, text=True)
                    ready = task == 'retry-control' and attempt >= 5
                    self.assertEqual(result.returncode, 0 if ready else 1)
                (root / 'client.py').write_text('import subprocess, sys\nsys.exit(subprocess.call([sys.executable, "service.py"]))\n')
                self.assertEqual(sandbox.check(root, task)['status'], 'passed' if task == 'retry-control' else 'failed')
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                sandbox.prepare(root, task)
                self.assertFalse((root / '.requests').exists())
