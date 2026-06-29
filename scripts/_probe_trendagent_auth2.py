import json
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'app-id': 'trendagent',
})

phone = '+79650412059'
password = 'N7FXpa6'

payloads = [
    {'phone': phone, 'password': password},
    {'login': phone, 'password': password},
    {'phone': phone.replace('+', ''), 'password': password},
    {'phone': '79650412059', 'password': password},
    {'username': phone, 'password': password},
]

urls = [
    'https://auth.trendagent.ru/',
    'https://auth.trendagent.ru/login',
    'https://auth.trendagent.ru/signin',
    'https://auth.trendagent.ru/api/signin',
    'https://auth.trendagent.ru/api/auth/login',
    'https://sso-api.trend.tech/v1/auth/login',
    'https://sso-api.trend.tech/v1/login',
    'https://sso-api.trend.tech/auth/login',
    'https://sso-api-registration.trendagent.ru/v1/login',
]

for url in urls:
    for payload in payloads[:2]:
        try:
            r = session.post(url, json=payload, timeout=20)
            if r.status_code not in (404, 405):
                print('POST', url, r.status_code, payload.keys(), r.text[:400])
        except Exception as e:
            print('ERR', url, e)

# GET auth root with query
for params in [
    {'phone': phone, 'password': password},
    {'login': phone, 'password': password},
]:
    r = session.get('https://auth.trendagent.ru/', params=params, timeout=20)
    print('GET auth/', r.status_code, r.text[:300])

# try apartment-api without auth
for path in ['/', '/blocks', '/apartments', '/v1/blocks', '/search']:
    url = 'https://apartment-api.trendagent.ru' + path
    try:
        r = session.get(url, timeout=15)
        print('apartment', path, r.status_code, r.text[:200])
    except Exception as e:
        print('apartment err', path, e)

for path in ['/', '/blocks', '/search', '/v1/blocks']:
    url = 'https://house-api.trendagent.ru' + path
    try:
        r = session.get(url, timeout=15)
        print('house', path, r.status_code, r.text[:200])
    except Exception as e:
        print('house err', path, e)
