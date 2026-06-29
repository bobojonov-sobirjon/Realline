import re
cfg = open('data/spb_config.js', encoding='utf-8').read()
patterns = set()
for m in re.findall(r'["\'](/[a-zA-Z0-9_/-]{3,80})["\']', cfg):
    if any(x in m for x in ['block', 'apart', 'search', 'unit', 'layout', 'estate', 'complex']):
        patterns.add(m)
for m in re.findall(r'https://[a-zA-Z0-9._/-]+', cfg):
    if 'apartment' in m or 'house-api' in m:
        patterns.add(m)
for p in sorted(patterns):
    print(p)
