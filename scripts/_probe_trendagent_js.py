import re
import requests

session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0'

# download several chunks from trendagent
urls = [
    'https://trendagent.ru/_next/static/chunks/main-app-5505d2949a6b9d7b.js',
    'https://trendagent.ru/_next/static/chunks/352-f4c96bade566c353.js',
    'https://trendagent.ru/_next/static/chunks/806-dd2d22f03ee85fd0.js',
]
patterns = []
for url in urls:
    try:
        r = session.get(url, timeout=30)
        text = r.text
        for m in re.findall(r'https://[a-zA-Z0-9._/-]+', text):
            if 'trend' in m and any(x in m for x in ['auth', 'login', 'apartment', 'house', 'sso']):
                patterns.append(m)
        for m in re.findall(r'/[a-zA-Z0-9_/-]{4,80}', text):
            if any(x in m for x in ['login', 'auth', 'sign', 'token', 'apartment', 'block']):
                patterns.append(m)
    except Exception as e:
        print('err', url, e)

for p in sorted(set(patterns)):
    print(p)
