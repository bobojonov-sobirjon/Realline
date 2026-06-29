import re
import requests

r = requests.get('https://modules.trendagent.ru/env/env.production.js', timeout=30)
open('data/trendagent_env.js', 'w', encoding='utf-8').write(r.text)
keys = re.findall(r"([A-Z_]+)\s*:\s*['\"]([^'\"]+)['\"]", r.text)
for k, v in keys:
    print(k, '=', v)
print('---URLS---')
for u in sorted(set(re.findall(r'https?://[a-zA-Z0-9._/-]+', r.text))):
    print(u)
