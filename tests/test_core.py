import unittest
from loopguard.core import Detector, normalize
from loopguard.decision import parse


class Core(unittest.TestCase):
    def test_repetition_progress(self):
        d = Detector()
        e = dict(kind='tool_end', tool='shell', arguments='test', result='error')
        self.assertIsNone(d.observe(e))
        self.assertIsNone(d.observe(e))
        self.assertIsNotNone(d.observe(e))
        d.observe(dict(progress=True))
        self.assertIsNone(d.observe(e))
        for i in range(30):
            self.assertIsNone(d.observe(dict(e, result=i)))

    def test_missing_and_unknown(self):
        self.assertIsNone(normalize(dict(type='future')))
        d = Detector()
        for _ in range(4):
            self.assertIsNone(d.observe(dict(kind='tool_end', tool='mcp', arguments={})))
        with self.assertRaises(ValueError):
            normalize(dict(kind='usage', output_tokens=-1))

    def test_invalid_probability(self):
        for p in [-1, 2, True, '0.9']:
            with self.assertRaises(ValueError):
                parse({'answers': {'stop': {'type': 'noul', 'noul': p}}})
