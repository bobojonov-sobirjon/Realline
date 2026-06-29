# -*- coding: utf-8 -*-
import json
import os
import requests

phone = os.environ.get('TRENDAGENT_PHONE', '+79650412059')
password = os.environ.get('TRENDAGENT_PASSWORD', 'N7FXpa6')
s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})
login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=60).json()
token = login['auth_token']
city = '58c665588b6aa52311afa01b'
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'
block_id = '5fbbc8b7a4336b0008df6fda'

tests = [
    {'block_id': block_id, 'count': 50, 'offset': 0},
    {'block_id': block_id, 'limit': 50, 'offset': 0},
    {'block': block_id, 'count': 50, 'offset': 0},
    {'blocks': block_id, 'count': 50, 'offset': 0},
    {'query': 'Аструм', 'count': 50, 'offset': 0},
    {'text': 'Аструм', 'count': 50, 'offset': 0},
    {'block_name': 'Аструм', 'count': 50, 'offset': 0},
]

for params in tests:
    r = s.get(f'{base}/apartments/search', headers=headers, params={'city': city, **params}, timeout=60)
    d = r.json().get('data') or {}
    lst = d.get('list') or []
    names = {x.get('block_name') for x in lst[:10]}
    print(params, '->', 'count', d.get('apartmentsCount'), 'page', len(lst), 'blocks', names)

for path in [
    f'/blocks/{block_id}/apartments',
    f'/blocks/{block_id}/units',
    f'/apartments/block/{block_id}',
]:
    r = s.get(base + path, headers=headers, params={'city': city, 'count': 50, 'offset': 0}, timeout=60)
    print(path, r.status_code, r.text[:200].replace('\n', ' '))
