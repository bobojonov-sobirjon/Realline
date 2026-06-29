import json
import requests

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})

phone = '+79650412059'
password = 'N7FXpa6'

r = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=30)
print('login', r.status_code)
data = r.json()
print(json.dumps({k: (v[:80] + '...' if isinstance(v, str) and len(v) > 80 else v) for k, v in data.items()}, ensure_ascii=False, indent=2))

token = data.get('access_token') or data.get('token')
refresh = data.get('refresh_token')
auth_header = {'Authorization': f'Bearer {token}'} if token else {}

# try refresh if only refresh_token
if not token and refresh:
    r2 = s.post('https://sso-api.trendagent.ru/v1/refresh', json={'refresh_token': refresh}, timeout=30)
    print('refresh', r2.status_code, r2.text[:500])
    if r2.ok:
        data2 = r2.json()
        token = data2.get('access_token') or data2.get('token')
        auth_header = {'Authorization': f'Bearer {token}'}

headers = {**s.headers, **auth_header}
print('token prefix', (token or '')[:40])

bases = [
    'https://apartment-api.trendagent.ru',
    'https://house-api.trendagent.ru',
    'https://api.trendagent.ru/v4_29',
]

paths = [
    '/blocks', '/block', '/search/blocks', '/v1/blocks', '/v2/blocks',
    '/apartments', '/search', '/v1/search', '/v2/search',
    '/estates', '/complexes', '/houses',
]

for base in bases:
    for path in paths:
        url = base + path
        try:
            for params in [{}, {'city': 'spb'}, {'region': 'spb'}, {'limit': 5}]:
                r = s.get(url, headers=headers, params=params, timeout=20)
                if r.status_code == 200 and r.text and r.text[0] in '{[':
                    print('OK', url, params, r.text[:300])
                    break
                elif r.status_code not in (401, 403, 404, 405):
                    print('?', url, r.status_code, r.text[:120])
        except Exception as e:
            pass

# search by name
name = 'Аструм'
for base in ['https://apartment-api.trendagent.ru', 'https://house-api.trendagent.ru']:
    for path in ['/search', '/blocks/search', '/v1/search/blocks', '/v2/blocks/search']:
        url = base + path
        for params in [{'query': name}, {'name': name}, {'q': name}, {'text': name}]:
            try:
                r = s.get(url, headers=headers, params=params, timeout=20)
                if r.status_code == 200:
                    print('SEARCH', url, params, r.text[:400])
            except Exception:
                pass

open('data/login_response.json', 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=2))
