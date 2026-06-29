import json
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'TrendAgent/1.0 Android',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
})

phone = '+79650412059'
password = 'N7FXpa6'

tests = [
    ('GET', 'https://auth.trendagent.ru/', None, {}),
    ('POST', 'https://auth.trendagent.ru/', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://auth.trendagent.ru/', {'phone': phone, 'password': password, 'client': 'android'}, {}),
    ('POST', 'https://auth.trendagent.ru/', {'phone': phone, 'password': password}, {'client': 'android'}),
    ('POST', 'https://auth.trendagent.ru/', {'phone': phone, 'password': password}, {'app-id': 'android'}),
    ('POST', 'https://auth.trendagent.ru/signin', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://auth.trendagent.ru/api/v1/auth', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://auth.trendagent.ru/api/v1/auth/login', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://auth.trendagent.ru/api/v1/auth/signin', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://auth.trendagent.ru/api/v1/users/auth', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://user-api.trendagent.ru/v1/auth/signin', {'phone': phone, 'password': password}, {'Authorization': 'Bearer '}),
    ('POST', 'https://user-api.trendagent.ru/api/v1/auth/signin', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://api.trendagent.ru/v4_29/auth/signin', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://api.trendagent.ru/v4_29/users/signin', {'phone': phone, 'password': password}, {}),
    ('POST', 'https://api.trendagent.ru/v4_29/login', {'phone': phone, 'password': password}, {}),
]

out = []
for method, url, payload, extra_headers in tests:
    headers = {**session.headers, **extra_headers}
    try:
        if method == 'GET':
            r = session.get(url, headers=headers, timeout=20)
        else:
            r = session.post(url, json=payload, headers=headers, timeout=20)
        out.append({
            'url': url,
            'method': method,
            'status': r.status_code,
            'body': r.text[:1000],
            'headers': dict(r.headers),
        })
    except Exception as e:
        out.append({'url': url, 'error': str(e)})

open('data/auth_probe4.json', 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=2))
for item in out:
    print(item.get('url'), item.get('status'), (item.get('body') or item.get('error', ''))[:200])
