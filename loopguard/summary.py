"""Deterministic evidence summary; no model call or inferred progress."""
from collections import deque
import hashlib
import json
import re

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def clean(value):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False)
    return ANSI.sub('', text).replace('\r\n', '\n').replace('\r', '\n').strip()


def excerpt(text, limit):
    # Collapse adjacent duplicate lines while preserving order and repetition counts.
    lines = []
    previous, count = None, 0
    for line in text.splitlines():
        if line == previous:
            count += 1
        else:
            if previous is not None:
                lines.append(previous + (f' [x{count}]' if count > 1 else ''))
            previous, count = line, 1
    if previous is not None:
        lines.append(previous + (f' [x{count}]' if count > 1 else ''))
    compact = '\n'.join(lines)
    if len(compact) > limit:
        return compact[:limit//2] + '\n[…]\n' + compact[-limit//2:]
    return compact


class TraceSummary:
    def __init__(self):
        self.recent = deque(maxlen=16)
        self.tools = self.progress_count = 0
        self.last_progress = None

    def observe(self, seq, event):
        if event.get('progress') is True:
            self.progress_count += 1
            self.last_progress = seq
            self.recent.clear()
        if event.get('kind') != 'tool_end':
            return
        self.tools += 1
        args, result = clean(event.get('arguments')), clean(event.get('result'))
        key = json.dumps([event.get('tool'), args, result, event.get('failed')], ensure_ascii=False)
        self.recent.append(dict(seq=seq, fingerprint=hashlib.sha256(key.encode()).hexdigest(),
                                tool=str(event.get('tool', 'unknown'))[:80],
                                arguments=excerpt(args, 160), outcome=excerpt(result, 320),
                                outcome_truncated=len(result) > 320,
                                failed=event.get('failed')))

    def build(self, trigger, max_bytes=6000):
        groups = {}
        for event in self.recent:
            key = event['fingerprint']
            if key not in groups:
                groups[key] = dict(event, evidence_ids=[], count=0)
                del groups[key]['seq']
            groups[key]['count'] += 1
            groups[key]['evidence_ids'].append(event['seq'])
        ranked = sorted(groups.values(), key=lambda x: (x['count'], x['evidence_ids'][-1]), reverse=True)
        state = dict(trigger=trigger, total_tool_calls=self.tools,
                     window_tool_calls=len(self.recent), explicit_progress_count=self.progress_count,
                     last_explicit_progress_event=self.last_progress,
                     progress_status='unknown' if self.last_progress is None else 'explicit_signal_observed',
                     limitations=['Task objective unavailable; absent progress signals do not prove no progress.',
                                  'Excerpts are lossy and unredacted; fingerprints compare normalized full outcomes.'],
                     patterns=ranked, omitted_patterns=0)
        while len(json.dumps(state, ensure_ascii=False).encode()) > max_bytes and state['patterns']:
            state['patterns'].pop()
            state['omitted_patterns'] += 1
        return state
