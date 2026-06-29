# -*- coding: utf-8 -*-
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

login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': '+79650412059', 'password': 'N7FXpa6'}, timeout=30).json()
token = login['auth_token']
city = login['user']['agency']['city']['_id']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

base_params = {'city': city, 'show_type': 'list', 'count': 20, 'offset': 0}
extras = [
    {},
    {'rooms': [0, 1, 2, 3, 4, 22, 23, 24, 25]},
    {'price_from': 0, 'price_to': 999999999},
    {'status': 1},
    {'type': 1},
    {'object_type': 1},
    {'is_suite': 0},
    {'deadline_key': 'all'},
    {'sort': 'price'},
    {'sort': 'name'},
    {'sort_type': 'asc'},
    {'text': 'Аструм'},
    {'query': 'Аструм'},
]

for extra in extras:
    params = {**base_params, **extra}
    r = s.get(base + '/blocks/search', headers=headers, params=params, timeout=30)
    if not r.ok:
        print('FAIL', extra, r.status_code, r.text[:150])
        continue
    lst = (r.json().get('data') or {}).get('list') or []
    print('OK', extra, 'count', len(lst), 'sample', (lst[0].get('name') if lst else None))

# POST blocks/search
r = s.post(base + '/blocks/search', headers=headers, json={**base_params, 'text': 'Аструм'}, timeout=30)
print('POST', r.status_code, r.text[:300])
