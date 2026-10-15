# -*- coding: utf-8 -*-
"""精查：会话日志里「中断」前后到底发生了什么（只看事件 type 与关键帧）。"""
import collections
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
P = (r"C:\Users\Administrator\.dsh\sessions"
     r"\--D-DSH-~519B~4E8B~6E38~620F~6C49~5316--"
     r"\session-863ea4b4-fb74-4684-a519-3e3acb95003b\session.v4.jsonl.zstd")
from compression import zstd

raw = zstd.decompress(open(P, "rb").read())
evs = []
for l in raw.decode("utf-8", "replace").split("\n"):
    if not l.strip():
        continue
    try:
        evs.append(json.loads(l))
    except Exception:
        pass
print("事件 %d" % len(evs))
print("type 分布:", dict(collections.Counter(e.get("type") for e in evs)))

# 找 read gen_txt_zh 的那次调用，以及它之后到用户提问之间的所有事件
idx = None
for i, e in enumerate(evs):
    d = e.get("data") or {}
    s = json.dumps(d, ensure_ascii=False)
    if "gen_txt_zh.py" in s and e.get("type") == "tool/call":
        idx = i
print("\nread gen_txt_zh 调用序号:", idx)
if idx is not None:
    for e in evs[idx - 1: idx + 6]:
        d = e.get("data") or {}
        t = e.get("type")
        msg = d.get("message") or {}
        role = msg.get("role")
        brief = json.dumps(msg, ensure_ascii=False)[:220]
        print("  seq=%s type=%-26s turn=%s step=%s role=%s %s"
              % (e.get("seq"), t, d.get("turn"), d.get("step"), role, brief))

# 所有非「常规」事件（可能是中断/取消/错误标记）
COMMON = {"assistant/message", "tool/call", "tool/result", "session-log-deepseek/delivery-accepted"}
print("\n非寻常事件：")
for e in evs:
    if e.get("type") not in COMMON:
        d = e.get("data") or {}
        print("  seq=%-5s type=%-34s %s" % (e.get("seq"), e.get("type"),
              json.dumps(d, ensure_ascii=False)[:200]))
