import json
import re
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Origin': 'https://trendagent.ru',
    'Referer': 'https://trendagent.ru/',
})

phone = '+79650412059'
password = 'N7FXpa6'

# SSO endpoints from env.js
sso_tests = [
    ('POST', 'https://sso-api.trend.tech/v1/auth/sign-in', {'phone': phone, 'password': password}),
    ('POST', 'https://sso-api.trend.tech/v1/auth/sign-in', {'login': phone, 'password': password}),
    ('POST', 'https://sso-api.trend.tech/v1/auth/sign-in', {'phone': '79650412059', 'password': password}),
    ('POST', 'https://sso-api.trend.tech/v1/auth/login', {'phone': phone, 'password': password}),
    ('POST', 'https://sso-api.trend.tech/v1/users/login', {'phone': phone, 'password': password}),
    ('POST', 'https://sso-api-registration.trendagent.ru/v1/auth/sign-in', {'phone': phone, 'password': password}),
    ('POST', 'https://sso-api-registration.trendagent.ru/v1/login', {'phone': phone, 'password': password}),
]

for method, url, payload in sso_tests:
    for headers in [
        {},
        {'client': 'web'},
        {'x-client': 'web'},
        {'app-id': 'trendagent'},
        {'X-App-Id': 'trendagent'},
        {'client-id': 'trendagent'},
    ]:
        h = {**session.headers, **headers}
        try:
            r = session.post(url, json=payload, headers=h, timeout=20)
            if r.status_code not in (404, 405):
                print(url, headers, r.status_code, r.text[:500])
        except Exception as e:
            print('ERR', url, e)

# auth.trendagent.ru POST variants
auth_payloads = [
    {'phone': phone, 'password': password},
    {'phone': '79650412059', 'password': password},
    {'login': phone, 'password': password},
]
for path in ['/', '/signin', '/sign-in', '/api/signin', '/api/sign-in', '/api/auth/sign-in']:
    for payload in auth_payloads:
        try:
            r = session.post('https://auth.trendagent.ru' + path, json=payload, timeout=20)
            if r.status_code not in (404, 405):
                print('auth', path, r.status_code, r.text[:400])
        except Exception as e:
            print('auth err', path, e)

# search JS bundles
chunks = [
    'https://trendagent.ru/_next/static/chunks/352-f4c96bade566c353.js',
    'https://trendagent.ru/_next/static/chunks/806-dd2d22f03ee85fd0.js',
]
found = set()
for url in chunks:
    r = session.get(url, timeout=30)
    for m in re.findall(r'sign-?in|/auth[a-zA-Z/_-]{0,40}|apartment-api[a-zA-Z/_-]{0,40}', r.text, re.I):
        found.add(m)
print('JS hints:', sorted(found)[:40])
