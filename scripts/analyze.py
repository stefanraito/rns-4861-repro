#!/usr/bin/env python3
"""Replay a wrapwatch log and report wrappers whose native height disagrees with Fabric's cache."""
import re, sys

cache, frame, owner = {}, {}, {}
lines = open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/wrapwatch.txt').read().splitlines()
verbose = '-v' in sys.argv
for n, line in enumerate(lines, 1):
    m = re.match(r'W (\w+) updateLayoutMetrics new=\(\S+ \S+; (\S+) (\S+)\)', line)
    if m:
        cache[m[1]] = float(m[3]); continue
    m = re.match(r'W (\w+) (setBounds|setFrame ) \(\S+ \S+; (\S+) (\S+)\)\s+(.*)', line)
    if m:
        w, h = m[1], float(m[4])
        if h == 0: continue
        src = 'fabric' if 'updateLayoutMetrics' in m[5] else 'uikit'
        frame[w] = h
        if verbose or (w in cache and cache[w] != h):
            print(f'{n:5} {w} {src:6} frame->{h:g} cache={cache.get(w)}')
        continue
    m = re.match(r'W (\w+) prepareForRecycle', line)
    if m:
        w = m[1]
        tag = 'STALE' if cache.get(w) != frame.get(w) else 'ok'
        print(f'{n:5} {w} recycled frame={frame.get(w)} cache={cache.get(w)} {tag}')
print('final:')
for w in frame:
    tag = 'STALE' if cache.get(w) != frame.get(w) else ''
    print(f'  {w} frame={frame[w]:g} cache={cache.get(w)} {tag}')
