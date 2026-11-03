"""Harness-neutral events and bounded repetition detection."""
import json
from collections import deque

FIELDS = set('kind tool arguments result failed progress input_tokens output_tokens context_tokens generation_ms gap_ms'.split())


# Capabilities describe adapter evidence, not inferred model behavior.
CAPABILITIES = {
    'generic': dict(usage='optional_interval', progress='optional_explicit'),
    'codex': dict(usage='turn_completed_only', progress='unknown'),
}


def normalize(v, adapter='auto'):
    if not isinstance(v, dict):
        raise ValueError('expected event object')
    if adapter not in ('auto', *CAPABILITIES):
        raise ValueError('unknown adapter')
    if adapter == 'generic' and 'kind' not in v:
        raise ValueError('generic adapter requires kind')
    if adapter == 'codex':
        return normalize_codex(v)
    if 'kind' in v:
        if set(v) - FIELDS or not isinstance(v['kind'], str):
            raise ValueError('invalid generic event')
        for key in ('input_tokens', 'output_tokens', 'context_tokens', 'generation_ms', 'gap_ms'):
            if v.get(key) is not None and (type(v[key]) is not int or v[key] < 0):
                raise ValueError(f'invalid {key}')
        for key in ('progress', 'failed'):
            if v.get(key) is not None and type(v[key]) is not bool:
                raise ValueError(f'invalid {key}')
        return v
    return normalize_codex(v)


def normalize_codex(v):
    if v.get('type') == 'turn.completed':
        return normalize(dict(kind='usage', **{k: v.get('usage', {}).get(k) for k in ('input_tokens', 'output_tokens')}))
    if v.get('type') == 'item.completed':
        i = v.get('item', {})
        if i.get('type') == 'command_execution':
            return dict(kind='tool_end', tool=i['type'], arguments=i.get('command'), result=i.get('aggregated_output'), failed=i.get('exit_code', 0) != 0 or i.get('status') == 'failed')
        if i.get('type') == 'mcp_tool_call':
            result = dict(result=i.get('result'), error=i.get('error')) if i.get('result') is not None or i.get('error') is not None else None
            return dict(kind='tool_end', tool=f"{i.get('server', '')}:{i.get('tool', '')}", arguments=i.get('arguments'), result=result, failed=i.get('status') == 'failed')
    if 'type' not in v:
        raise ValueError('expected kind or type')
    return None


class Detector:
    def __init__(self, repeats=3):
        self.repeats = repeats
        self.recent = deque(maxlen=16)

    def observe(self, event):
        if event.get('progress') is True:
            self.recent.clear()
            return None
        if event.get('kind') != 'tool_end' or any(event.get(k) is None for k in ('tool', 'arguments', 'result')):
            return None
        key = json.dumps([event.get(k) for k in ('tool', 'arguments', 'result', 'failed')], sort_keys=True)
        self.recent.append(key)
        if self.recent.count(key) >= self.repeats:
            return 'repeated_tool_arguments_and_result'
        return None
