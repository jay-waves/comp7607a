"""Deterministic local demo; no model or credentials required."""
import json
import time

for _ in range(10):
    print(json.dumps({"kind": "tool_end", "tool": "shell", "arguments": "pytest",
                      "result": "missing dependency", "failed": True}), flush=True)
    time.sleep(0.2)
