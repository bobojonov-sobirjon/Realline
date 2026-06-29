import re
import requests

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

for name, url in [
    ('sso', 'https://sso.trend.tech/'),
    ('landing', 'https://trendagent.ru/'),
]:
    r = s.get(url, timeout=30)
    text = r.text
    open(f'data/{name}_page.html', 'w', encoding='utf-8').write(text[:500000])
    patterns = set()
    for m in re.findall(r'https://[a-zA-Z0-9._/-]+', text):
        if any(x in m for x in ['auth', 'sso', 'login', 'sign', 'apartment', 'house-api']):
            patterns.add(m)
    for m in re.findall(r'/[a-zA-Z0-9_/-]{3,80}', text):
        if any(x in m.lower() for x in ['auth', 'login', 'sign', 'token']):
            patterns.add(m)
    print(name, 'patterns', len(patterns))
    for p in sorted(patterns)[:60]:
        print(' ', p)
