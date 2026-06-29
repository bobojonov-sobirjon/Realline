import json
import re
import requests

# probe auth endpoints
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
})

phone = '+79650412059'
password = 'N7FXpa6'

candidates = [
    ('POST', 'https://auth.trendagent.ru/api/login', {'phone': phone, 'password': password}),
    ('POST', 'https://auth.trendagent.ru/login', {'phone': phone, 'password': password}),
    ('POST', 'https://auth.trendagent.ru/api/v1/login', {'phone': phone, 'password': password}),
    ('POST', 'https://sso-api.trend.tech/api/login', {'phone': phone, 'password': password}),
    ('POST', 'https://sso-api.trend.tech/v1/login', {'phone': phone, 'password': password}),
    ('POST', 'https://api.trendagent.ru/v4_29/login', {'phone': phone, 'password': password}),
    ('POST', 'https://user-api.trendagent.ru/login', {'phone': phone, 'password': password}),
    ('POST', 'https://user-api.trendagent.ru/api/login', {'phone': phone, 'password': password}),
    ('POST', 'https://user-api.trendagent.ru/v1/login', {'phone': phone, 'password': password}),
]

for method, url, payload in candidates:
    try:
        r = session.post(url, json=payload, timeout=20)
        print(url, r.status_code, r.text[:300].replace('\n', ' '))
    except Exception as e:
        print(url, 'ERR', e)

print('\n--- OPTIONS on auth ---')
for url in ['https://auth.trendagent.ru/', 'https://auth.trendagent.ru/api', 'https://user-api.trendagent.ru/']:
    try:
        r = session.get(url, timeout=15)
        print(url, r.status_code, r.headers.get('content-type'), r.text[:200])
    except Exception as e:
        print(url, e)
