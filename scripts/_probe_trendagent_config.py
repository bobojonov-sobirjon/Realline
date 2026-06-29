import re
import requests

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'
base = 'https://spb.trendagent.ru'

paths = [
    '/config.js',
    '/scripts/public-importmap.js',
    '/scripts/init-values.js',
    '/scripts/common-deps.js',
    '/scripts/initialize.js',
]

for path in paths:
    r = s.get(base + path, timeout=30)
    fname = path.replace('/', '_').strip('_')
    open(f'data/spb_{fname}', 'w', encoding='utf-8').write(r.text)
    print(path, r.status_code, len(r.text), r.headers.get('content-type'))
    if 'js' in (r.headers.get('content-type') or '') or path.endswith('.js'):
        for m in sorted(set(re.findall(r'https://[a-zA-Z0-9._/-]+', r.text))):
            if any(x in m for x in ['auth', 'sso', 'apartment', 'house', 'login']):
                print('  url', m)
