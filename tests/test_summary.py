import json
import unittest
from loopguard.summary import TraceSummary, excerpt

class Summary(unittest.TestCase):
    def test_grouping_and_progress(self):
        s = TraceSummary()
        for i in range(3):
            s.observe(i, dict(kind='tool_end', tool='shell', arguments='test', result='\x1b[31merror\x1b[0m\r\n', failed=True))
        state = s.build('repeat')
        self.assertEqual(state['patterns'][0]['count'], 3)
        self.assertEqual(state['patterns'][0]['evidence_ids'], [0, 1, 2])
        self.assertEqual(state['patterns'][0]['outcome'], 'error')
        self.assertEqual(state['progress_status'], 'unknown')
        s.observe(3, dict(kind='progress', progress=True))
        self.assertEqual(s.build('repeat')['patterns'], [])

    def test_budget_and_full_result_identity(self):
        s = TraceSummary()
        for i in range(30):
            s.observe(i, dict(kind='tool_end', tool='工具', arguments='参'*1000, result='x'*1000+str(i)+'y'*1000))
        state = s.build('repeat')
        self.assertLessEqual(len(json.dumps(state, ensure_ascii=False).encode()), 6000)
        self.assertTrue(all(p['count'] == 1 for p in state['patterns']))
        self.assertGreater(state['omitted_patterns'], 0)
        self.assertEqual(excerpt('error\nerror\nerror', 100), 'error [x3]')
