import re
import requests

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

for base in ['https://spb.trendagent.ru', 'https://msk.trendagent.ru']:
    r = s.get(base + '/static/js/bootstrap.js', timeout=30)
    print(base, 'bootstrap', r.status_code, len(r.text))
    open(f'data/{base.split("//")[1].split(".")[0]}_bootstrap.js', 'w', encoding='utf-8').write(r.text)
    for m in sorted(set(re.findall(r'https://[a-zA-Z0-9._/-]+', r.text))):
        if any(x in m for x in ['api', 'auth', 'sso', 'apartment', 'house']):
            print(' ', m)
    for m in sorted(set(re.findall(r'/[a-zA-Z0-9_/-]{4,80}', r.text))):
        if any(x in m.lower() for x in ['auth', 'login', 'sign', 'apartment', 'block', 'search']):
            print(' path', m)

# trend.tech env
r = s.get('https://modules.trend.tech/env/env.production.js', timeout=30)
open('data/trend_tech_env.js', 'w', encoding='utf-8').write(r.text)
print('trend.tech env', len(r.text))
